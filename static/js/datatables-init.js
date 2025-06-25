/ Simple table utilities without jQuery/DataTables
// Enables sorting by clicking on table headers and filtering by severity

function initSimpleTable() {
  const table = document.getElementById('vuln-table');
  if (!table) return;
  const tbody = table.tBodies[0];
  const originalRows = Array.from(tbody.rows);

  // Sorting
  const ths = table.tHead.rows[0].cells;
  Array.from(ths).forEach((th, i) => {
    if (i === 0 || i === 5) return; // skip non-sortable columns
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const rows = Array.from(tbody.rows);
      const sorted = rows.sort((a, b) => {
        const at = a.cells[i].textContent.trim();
        const bt = b.cells[i].textContent.trim();
        return at.localeCompare(bt, undefined, {numeric: true});
      });
      tbody.append(...sorted);
    });
  
  });

  // Severity filter
  const filter = document.getElementById('severity-filter');
  if (filter) {
    filter.addEventListener('change', (e) => {
      const val = e.target.value;
      originalRows.forEach(row => {
        const cellText = row.cells[3].textContent.trim();
        row.style.display = val === '' || cellText === val ? '' : 'none';
      });
    });
  }
}

document.addEventListener('DOMContentLoaded', initSimpleTable);