(function () {
  const clientName = window.clientName || "Unknown";
  let activeClocks =
    window.activeClocksCount !== undefined ? window.activeClocksCount : 1;
  let runningClocks =
    window.runningClocksCount !== undefined ? window.runningClocksCount : 0;

  const debugInfo = document.createElement("div");
  debugInfo.style.cssText =
    "position:fixed;bottom:10px;left:10px;font-size:12px;background:rgba(0,0,0,0.7);color:white;padding:5px;border-radius:3px;font-family:monospace;z-index:1000";
  document.body.appendChild(debugInfo);

  window.updateDebugInfo = function () {
    // Update counts if they're dynamic
    activeClocks =
      window.activeClocksCount !== undefined
        ? window.activeClocksCount
        : activeClocks;
    runningClocks =
      window.runningClocksCount !== undefined
        ? window.runningClocksCount
        : runningClocks;

    let wsStatus = "Disconnected";
    if (window.wsConnected !== undefined) {
      wsStatus = window.wsConnected ? "Connected" : "Disconnected";
    } else if (window.wsStatus) {
      // Handle string status from index page
      wsStatus =
        window.wsStatus.charAt(0).toUpperCase() + window.wsStatus.slice(1);
    }

    const reconnectBtn =
      wsStatus === "Disconnected" || wsStatus === "Error"
        ? '<button onclick="if(window.ws) { window.ws.close(); } window.connect && window.connect();" style="margin-top:5px;font-size:11px;padding:2px 5px;background:#555;color:white;border:none;border-radius:2px;cursor:pointer;">Reconnect</button>'
        : "";
    const disconnectBtn =
      wsStatus === "Connected"
        ? '<button onclick="window.manualDisconnect && window.manualDisconnect();" style="margin-top:5px;margin-left:5px;font-size:11px;padding:2px 5px;background:#d32f2f;color:white;border:none;border-radius:2px;cursor:pointer;">Disconnect</button>'
        : "";

    debugInfo.innerHTML = `
      Client: ${clientName}<br>
      WS Status: ${wsStatus}<br>
      Active Clocks: ${activeClocks}<br>
      Running Clocks: ${runningClocks}<br>
      ${reconnectBtn}${disconnectBtn}<br>
      Time: ${new Date().toLocaleString()}
    `;
  };

  // Update every second for live time
  setInterval(window.updateDebugInfo, 1000);

  // Initial update
  window.updateDebugInfo();
})();
