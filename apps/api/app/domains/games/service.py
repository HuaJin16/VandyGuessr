"""Game service containing all gameplay business logic."""

from datetime import UTC, datetime, timedelta

import structlog

from app.domains.games.daily import (
    ROUNDS_PER_GAME,
    DailyChallengeEntity,
    IDailyChallengeRepository,
    pick_daily_images,
    today_cst,
)
from app.domains.games.entities import GameEntity, RoundEntity
from app.domains.games.repository import IGameRepository
from app.domains.images.repository import IImageRepository
from app.domains.locations.service import LocationService
from app.shared.scoring import compute_score, haversine

logger = structlog.get_logger()


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Attach UTC tzinfo to naive datetimes from legacy documents."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


TIMED_ROUND_SECONDS = 120
TIMED_GRACE_SECONDS = 2  # network latency buffer for timed round expiry
UNTIMED_TIMEOUT_SECONDS = 3600  # 1 hour inactivity timeout


class GameError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GameService:
    def __init__(
        self,
        game_repository: IGameRepository,
        image_repository: IImageRepository,
        daily_challenge_repository: IDailyChallengeRepository,
        location_service: LocationService,
    ) -> None:
        self.game_repo = game_repository
        self.image_repo = image_repository
        self.daily_repo = daily_challenge_repository
        self.location_service = location_service

    async def start_game(
        self,
        user_id: str,
        timed: bool,
        environment: str,
        daily: bool,
    ) -> dict:
        """Create a new game with 5 rounds of randomly selected images."""
        # Check for existing active game
        existing = await self.game_repo.find_active_by_user(user_id)
        if existing:
            raise GameError("You already have an active game. Finish or end it first.")

        images = await self._select_images(environment, daily)
        if len(images) < ROUNDS_PER_GAME:
            raise GameError(
                f"Not enough images available (need {ROUNDS_PER_GAME}, "
                f"found {len(images)})."
            )

        now = datetime.now(UTC)
        rounds = [
            RoundEntity(
                round_id=i + 1,
                image_id=str(img["_id"]),
                image_url=img["url"],
                actual_lat=img["latitude"],
                actual_lng=img["longitude"],
                location_name=img.get("location_name"),
            )
            for i, img in enumerate(images)
        ]

        # Mark the first round as started
        rounds[0].started_at = now
        if timed:
            rounds[0].expires_at = now + timedelta(seconds=TIMED_ROUND_SECONDS)

        game = GameEntity(
            user_id=user_id,
            mode={"timed": timed, "environment": environment, "daily": daily},
            rounds=rounds,
            created_at=now,
            last_activity_at=now,
        )

        game_id = await self.game_repo.create(game)

        logger.info(
            "game_started",
            game_id=game_id,
            user_id=user_id,
            timed=timed,
            environment=environment,
            daily=daily,
        )

        return await self._reload(game_id)

    async def get_game(self, game_id: str, user_id: str) -> dict:
        """Retrieve a game, verifying ownership and handling expiry."""
        doc = await self._load_game(game_id, user_id)
        await self._check_expiry(doc)
        return doc

    async def start_round(self, game_id: str, user_id: str, round_number: int) -> dict:
        """Start the current playable round when the user enters it."""
        doc = await self._load_game(game_id, user_id)
        await self._check_expiry(doc)

        if doc["status"] != "active":
            raise GameError("This game is no longer active.", 409)

        round_index = round_number - 1
        if round_index < 0 or round_index >= len(doc["rounds"]):
            raise GameError(f"Invalid round number: {round_number}")

        rd = doc["rounds"][round_index]
        if rd.get("guess"):
            raise GameError(f"Round {round_number} already has a guess.", 409)
        if rd.get("skipped"):
            raise GameError(f"Round {round_number} was skipped.", 409)

        playable_index = next(
            (
                i
                for i, candidate in enumerate(doc["rounds"])
                if not candidate.get("guess") and not candidate.get("skipped")
            ),
            None,
        )
        if playable_index is None:
            raise GameError("This game is no longer active.", 409)
        if playable_index != round_index:
            raise GameError(f"Round {round_number} is not ready to start.", 409)

        if rd.get("started_at"):
            return doc

        now = datetime.now(UTC)
        round_update: dict = {"started_at": now}
        if doc["mode"].get("timed"):
            round_update["expires_at"] = now + timedelta(seconds=TIMED_ROUND_SECONDS)

        await self.game_repo.update_round(game_id, round_index, round_update)
        await self.game_repo.update_game(game_id, {"last_activity_at": now})
        return await self._reload(game_id)

    async def list_games(
        self,
        user_id: str,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        docs = await self.game_repo.find_by_user(user_id, status, limit, offset)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    async def submit_guess(
        self,
        game_id: str,
        user_id: str,
        round_number: int,
        lat: float,
        lng: float,
    ) -> dict:
        """Process a guess for a specific round."""
        doc = await self._load_game(game_id, user_id)
        await self._check_expiry(doc)

        if doc["status"] != "active":
            raise GameError("This game is no longer active.", 409)

        round_index = round_number - 1
        if round_index < 0 or round_index >= len(doc["rounds"]):
            raise GameError(f"Invalid round number: {round_number}")

        rd = doc["rounds"][round_index]
        if rd.get("guess"):
            raise GameError(f"Round {round_number} already has a guess.", 409)
        if rd.get("skipped"):
            raise GameError(f"Round {round_number} was skipped.", 409)

        # Check timed expiry for this specific round (with grace period)
        expires = _ensure_utc(rd.get("expires_at"))
        if expires and datetime.now(UTC) > expires + timedelta(
            seconds=TIMED_GRACE_SECONDS
        ):
            raise GameError(f"Round {round_number} has expired.", 409)

        distance = haversine(lat, lng, rd["actual_lat"], rd["actual_lng"])

        actual_building = rd.get("location_name")
        guess_building = await self.location_service.resolve_location_name(lat, lng)
        same_building = (
            actual_building is not None
            and guess_building is not None
            and actual_building == guess_building
        )
        score = compute_score(distance, same_building=same_building)

        now = datetime.now(UTC)
        round_update = {
            "guess": {"lat": lat, "lng": lng},
            "distance_meters": round(distance, 2),
            "score": score,
        }
        await self.game_repo.update_round(game_id, round_index, round_update)

        # Update game-level fields
        new_total = doc["total_score"] + score
        game_update: dict = {
            "total_score": new_total,
            "last_activity_at": now,
        }

        # Complete the game after the last round
        next_index = round_index + 1
        if next_index >= len(doc["rounds"]):
            game_update["status"] = "completed"

        await self.game_repo.update_game(game_id, game_update)

        if game_update.get("status") == "completed":
            doc["total_score"] = new_total

        logger.info(
            "guess_submitted",
            game_id=game_id,
            round=round_number,
            distance=round(distance, 2),
            score=score,
        )

        return await self._reload(game_id)

    async def end_game(self, game_id: str, user_id: str) -> dict:
        """End a game early, marking remaining rounds as skipped."""
        doc = await self._load_game(game_id, user_id)

        if doc["status"] != "active":
            raise GameError("This game is not active.", 409)

        now = datetime.now(UTC)
        for i, rd in enumerate(doc["rounds"]):
            if not rd.get("guess") and not rd.get("skipped"):
                await self.game_repo.update_round(game_id, i, {"skipped": True})

        await self.game_repo.update_game(
            game_id,
            {"status": "completed", "last_activity_at": now},
        )

        logger.info("game_ended_early", game_id=game_id, user_id=user_id)

        return await self._reload(game_id)

    async def find_active_game(self, user_id: str) -> dict | None:
        """Return the user's active game if one exists and hasn't expired."""
        doc = await self.game_repo.find_active_by_user(user_id)
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        await self._check_expiry(doc)
        if doc["status"] != "active":
            return None
        return doc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _reload(self, game_id: str) -> dict:
        """Re-fetch a game document after mutation, stringify its _id."""
        doc = await self.game_repo.find_by_id(game_id)
        if not doc:
            raise GameError("Game not found.", 404)
        doc["_id"] = str(doc["_id"])
        return doc

    async def _select_images(self, environment: str, daily: bool) -> list[dict]:
        """Pick images for a new game — daily or random."""
        if daily:
            return await self._daily_images()

        # Random: filter by environment if not "any"
        return await self.image_repo.sample_random(ROUNDS_PER_GAME, environment)

    async def _daily_images(self) -> list[dict]:
        """Get or create today's daily challenge image set."""
        date_str = today_cst()
        cached = await self.daily_repo.find_by_date(date_str)

        if cached:
            image_ids = cached["image_ids"]
        else:
            # Daily ignores environment filter per PRD
            all_ids = await self.image_repo.find_all_ids()
            if len(all_ids) < ROUNDS_PER_GAME:
                return []
            image_ids = pick_daily_images(date_str, all_ids)
            challenge = DailyChallengeEntity(date=date_str, image_ids=image_ids)
            await self.daily_repo.create(challenge)
            logger.info("daily_challenge_created", date=date_str, images=image_ids)

        return await self.image_repo.find_by_ids(image_ids)

    async def _load_game(self, game_id: str, user_id: str) -> dict:
        doc = await self.game_repo.find_by_id(game_id)
        if not doc:
            raise GameError("Game not found.", 404)
        doc["_id"] = str(doc["_id"])
        if doc["user_id"] != user_id:
            raise GameError("Game not found.", 404)
        return doc

    async def _check_expiry(self, doc: dict) -> None:
        """Reconcile active games: abandon on inactivity, skip expired timed rounds."""
        if doc["status"] != "active":
            return

        last = _ensure_utc(doc.get("last_activity_at"))
        if not last:
            return

        now = datetime.now(UTC)

        # Inactivity abandonment (applies to all modes)
        if now - last > timedelta(seconds=UNTIMED_TIMEOUT_SECONDS):
            await self.game_repo.update_game(
                doc["_id"], {"status": "abandoned", "last_activity_at": now}
            )
            doc["status"] = "abandoned"
            logger.info("game_auto_abandoned", game_id=doc["_id"])
            return

        # Timed-round reconciliation: skip rounds whose deadline has passed
        if not doc["mode"].get("timed"):
            return

        grace = timedelta(seconds=TIMED_GRACE_SECONDS)
        skipped_any = False

        for i, rd in enumerate(doc["rounds"]):
            expires = _ensure_utc(rd.get("expires_at"))
            if not expires:
                continue
            if rd.get("guess") or rd.get("skipped"):
                continue
            if now > expires + grace:
                await self.game_repo.update_round(
                    doc["_id"], i, {"skipped": True, "score": 0}
                )
                doc["rounds"][i]["skipped"] = True
                doc["rounds"][i]["score"] = 0
                skipped_any = True
                logger.info("round_auto_skipped", game_id=doc["_id"], round=i + 1)

        if not skipped_any:
            return

        # Find next playable round and start it, or complete the game
        next_index = next(
            (
                i
                for i, rd in enumerate(doc["rounds"])
                if not rd.get("guess") and not rd.get("skipped")
            ),
            None,
        )

        if next_index is not None:
            next_round_update = {
                "started_at": now,
                "expires_at": now + timedelta(seconds=TIMED_ROUND_SECONDS),
            }
            await self.game_repo.update_round(doc["_id"], next_index, next_round_update)
            doc["rounds"][next_index]["started_at"] = now
            doc["rounds"][next_index]["expires_at"] = now + timedelta(
                seconds=TIMED_ROUND_SECONDS
            )
        else:
            await self.game_repo.update_game(
                doc["_id"], {"status": "completed", "last_activity_at": now}
            )
            doc["status"] = "completed"
            logger.info("game_auto_completed", game_id=doc["_id"])

        await self.game_repo.update_game(doc["_id"], {"last_activity_at": now})
        doc["last_activity_at"] = now
