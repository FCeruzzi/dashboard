$(document).ready(function() {
    var table = $('#vuln-table').DataTable({
      dom: "<'row'<'col-sm-3'l><'col-sm-6'f><'col-sm-3'p>>rt<'row'<'col-sm-5'i><'col-sm-7'p>>",
      paging: true,
      ordering: true,
      info: true,
      columnDefs: [{ targets: [0,5], orderable: false }]
    });
  
    // filtro per severity
    $('#severity-filter').on('change', function() {
      table.column(3).search(this.value).draw();
    });
  });