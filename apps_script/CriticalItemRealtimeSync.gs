/**
 * FG_Order_Tracker Main → Critical Item
 * Updates ONLY columns D–G (Warehouse / Branch / Total / Daily Network Demand).
 *
 * Primary sync path: Cursor + Foodics MCP → data/critical_updates.json
 * Then either paste data/paste_DG.tsv into D3, or run applyCriticalUpdatesJson below.
 */

var SHEET_NAME = 'Critical Item';
var DATA_START = 3;
var COL_SKU = 2; // B
var COL_WAREHOUSE = 4; // D
var NUM_UPDATE_COLS = 4; // D–G

/**
 * @param {string} jsonText contents of data/critical_updates.json
 */
function applyCriticalUpdatesJson(jsonText) {
  var updates = JSON.parse(jsonText);
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('Sheet not found: ' + SHEET_NAME);

  var lastRow = sheet.getLastRow();
  if (lastRow < DATA_START) return;

  var n = lastRow - DATA_START + 1;
  var skus = sheet.getRange(DATA_START, COL_SKU, n, 1).getValues();
  var out = [];
  for (var i = 0; i < skus.length; i++) {
    var sku = String(skus[i][0] || '').trim();
    var u = updates[sku];
    if (!u) {
      out.push(['', '', '', '']);
      continue;
    }
    out.push([
      u.warehouse_stock,
      u.branch_stock,
      u.total_stock,
      u.daily_network_demand
    ]);
  }
  sheet.getRange(DATA_START, COL_WAREHOUSE, out.length, NUM_UPDATE_COLS).setValues(out);
}
