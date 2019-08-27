let userData;
$(document).ready(function () {
  _min_max_nav();
  userData = localStorage;
  nav_href('users');
});

function nav_mark(id){
  // loader(1);
  $('.sidenav > div > a').removeClass('active');
  $('#' + id).addClass('active');
}

function nav_href(t) {
  _loading(1);
  $('#mainBody').load('/page/' + t);
  nav_mark('nav_' + t);
}


function logout() {
  _loading(1);
  localStorage.clear();
  window.location.href = '/logout';
}

function alert(cls, msg) {
    let strong;
    if(cls === 'success'){
        strong = 'Success!';
    }else if(cls === 'info'){
        strong = 'Info!';
    }else{
        strong = 'Warning';
    }
    $('#alert').empty().append(
        '<div class="alert alert-' + cls + ' alert-dismissible fade in">' +
        '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>' +
        '<strong>' + strong + '</strong> ' + msg +
        '</div>'
    );
}

$('.sidenav > div > a._output_2').on('click', function () {
    $('.sidenav2').css('left', '-200px');
    var sidenav2_id = $(this).attr('id').split('_')[1];
    let status = $('#sidenav_1').attr('data-status');
    if(status === 'true'){
      $('#'+sidenav2_id).css('left', '200px');
    }else {
      $('#'+sidenav2_id).css('left', '50px');
    }
});

$('.sidenav2_close').click(function(){
  let status = $('#sidenav_1').attr('data-status');
  if(status === 'true'){
    $('.sidenav2').css('left', '0');
  }else{
    $('.sidenav2').css('left', '-200px');
  }
});

$('.sidenav2 > a').on('click', function () {
  let status = $('#sidenav_1').attr('data-status');
  if(status === 'true'){
    $('.sidenav2').css('left', '0');
  }else{
    $('.sidenav2').css('left', '-200px');
  }
});

$('.sidenav > div > a._output_3').on('click', function () {
    $('.sidenav3').css('left', '-200px');
    var sidenav3_id = $(this).attr('id').split('_')[1];
    let status = $('#sidenav_1').attr('data-status');
    if(status === 'true'){
      $('#'+sidenav3_id).css('left', '200px');
    }else {
      $('#'+sidenav3_id).css('left', '50px');
    }
});

$('.sidenav3_close').click(function(){
  let status = $('#sidenav_1').attr('data-status');
  if(status === 'true'){
    $('.sidenav3').css('left', '0');
  }else{
    $('.sidenav3').css('left', '-200px');
  }
});

$('.sidenav3 > a').on('click', function () {
  let status = $('#sidenav_1').attr('data-status');
  if(status === 'true'){
    $('.sidenav3').css('left', '0');
  }else{
    $('.sidenav3').css('left', '-200px');
  }
});

function _min_max_nav(){
  let status = $('#sidenav_1').attr('data-status');
  console.log(status);
  if(status === 'true'){
    $('#mainBody').css('padding-left', '50px');
    $('#sidenav_1').attr('data-status', 'false').css('width', '50px');
    $('#sidenav_1 > div > a').css('justify-content', 'center');
    $('#sidenav_1 > div > a > i').css('margin-right', '0');
    $('#sidenav_1 > div > a > p').css('display', 'none');
    $('#nav_max').css('justify-content', 'center');
    $('#nav_max > i').removeClass('fa-angle-left').addClass('fa-angle-right')
    .css('margin-right', '0');
    $('.sidenav2').css('left', '-200px');
    $('.sidenav3').css('left', '-200px');
  }else{
    $('#mainBody').css('padding-left', '200px');
    $('#sidenav_1').attr('data-status', 'true').css('width', '200px');
    $('#sidenav_1 > div > a').css('justify-content', 'start');
    $('#sidenav_1 > div > a > i').css('margin-right', '15px');
    $('#sidenav_1 > div > a > p').css('display', 'inherit');
    $('#nav_max').css('justify-content', 'flex-end');
    $('#nav_max > i').removeClass('fa-angle-right').addClass('fa-angle-left')
    .css('margin-right', '15px');
    $('.sidenav2').css('left', '0');
    $('.sidenav3').css('left', '0');
  }
}
