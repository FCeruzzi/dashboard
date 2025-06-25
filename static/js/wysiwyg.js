document.addEventListener('DOMContentLoaded', function () {
    var editor = document.getElementById('editor');
    var hiddenInput = document.getElementById('sal-text');
    var form = document.getElementById('sal-form');
  
    if (!editor || !form || !hiddenInput) return;
  
    // formatting buttons
    document.querySelectorAll('[data-cmd]').forEach(function(btn){
      btn.addEventListener('click', function(){
        var cmd = btn.getAttribute('data-cmd');
        document.execCommand(cmd, false, null);
        editor.focus();
      });
    });
  
    // handle tab key inside editor
    editor.addEventListener('keydown', function(e){
      if (e.key === 'Tab') {
        e.preventDefault();
        document.execCommand('insertText', false, '\t');
      }
    });
  
    // copy plain text before submit
    form.addEventListener('submit', function(){
      hiddenInput.value = editor.innerText;
    });    
  });