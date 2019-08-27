/**
 * Developed by ION Developer Team
 * URL : https://ION.id
 */

function _loading(t){
  if(t === 0){
    $('#panel-layer').css('opacity', 0);
      setTimeout(
        function(){
        $('#panel-layer').css('display', 'none')
      }, 1000);
  }else{
    $('#panel-layer').css('display', 'flex')
    setTimeout(
      function(){
      $('#panel-layer').css('opacity', 1);
    }, 100);
  }
}

function notif(type, title, content) {
  let icon;
  if(type === 'danger'){
    icon = 'close';
  }else if(type === 'notif'){
    icon = 'bell';
  }else if(type === 'success'){
    icon = 'check';
  }else if(type === 'warning'){
    icon = 'exclamation';
  }else if(type === 'info'){
    icon = 'info';
  }
  $('div#notification-box').append(
    '<div class="notification-box ' + type + '">' +
    '<div class="left"><i class="fa fa-' + icon + '"></i></div>' +
    '<div class="right ' + type + '">' +
    '<h5>' + title + '</h5>' +
    '<p>' + content + '</p>' +
    '</div>' +
    '<a onclick="close_notif(this)"><i class="glyphicon glyphicon-menu-right notif"></i></a>' +
    '</div>'
  );
}

function close_notif(t){
  $($(t).parent()).css('right', '-200%');
  setTimeout(
    function(){
      $($(t).parent()).remove();
  }, 300)
}
