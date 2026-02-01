<script lang="ts">
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

let healthStatus = "checking...";

async function checkHealth() {
	try {
		const response = await fetch(`${apiUrl}/api/v1/health`);
		const data = await response.json();
		healthStatus = data.status === "healthy" ? "Backend connected!" : "Backend unhealthy";
	} catch {
		healthStatus = "Backend not available";
	}
}

checkHealth();
</script>

<main class="min-h-screen bg-gradient-to-br from-vandy-black to-gray-900 flex items-center justify-center">
  <div class="text-center">
    <h1 class="text-5xl font-bold text-vandy-gold mb-4">VandyGuessr</h1>
    <p class="text-gray-300 text-xl mb-8">
      A GeoGuessr-style game for Vanderbilt University
    </p>
    <div class="bg-gray-800 rounded-lg p-6 max-w-md mx-auto">
      <p class="text-gray-400 mb-2">API Status:</p>
      <p class="text-lg font-mono {healthStatus.includes('connected') ? 'text-green-400' : 'text-yellow-400'}">
        {healthStatus}
      </p>
    </div>
    <p class="text-gray-500 mt-8 text-sm">
      Start the backend with: <code class="bg-gray-800 px-2 py-1 rounded">uv run uvicorn app.main:app --reload</code>
    </p>
  </div>
</main>
