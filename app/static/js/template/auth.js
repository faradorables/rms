/**
 * Developed by ION Developer Team
 * URL : https://ION.id
 */

function login() {
  _loading(0);
  $('input#view_pass').on('change', function () {
      if ($(this).is(':checked')) {
          $('input#password').attr('type', 'text');
      }else{
          $('input#password').attr('type', 'password');
      }
  })
  $('form').submit(function (e) {
      e.preventDefault();
      $.post('/api/v1/auth/login',{
          email: $('#email').val(),
          pin: $('#pin').val()
      }, function(result){
        console.log(result);
          if(result.status === '00'){
              localStorage.setItem('name', result.name);
              localStorage.setItem('id', result.user_id);
              localStorage.setItem('phone_number', result.phone_number);
              localStorage.setItem('email', result.email);
              localStorage.setItem('token', result.token);
              location.reload();
          }else{
              notif('danger', 'Authentication failed', result.message)
          }
      }).fail(function () {
        notif('warning', 'Authentication failed', 'Maaf, sistem sedang ada gangguan...')
      });
  })
}

function addadmin(){
  $('input#view_pass').on('change', function () {
      if ($(this).is(':checked')) {
          $('input#password').attr('type', 'text');
      }else{
          $('input#password').attr('type', 'password');
      }
  })
}

function change_password() {
    $('form').submit(function (e) {
        e.preventDefault();


        $.post('/request/auth-change-password',{
            old_password: $('#old_password').val(),
            password: $('#password').val(),
            password2: $('#password2').val()
        }, function(result){
            if(result.status === 0){
                loader(0)
            }else{
                location.replace(window.location.origin);
            }
            $('#notification-box > span').text(result.message)
        }).fail(function () {
            $('#notification-box > span').text('Maaf sistem sedang ada ada gangguan');
        });
        $('#notification-box').delay(200).fadeIn('slow').css('display', 'flex');

    })
}

function reset_password() {
    $('form').submit(function (e) {
        e.preventDefault();


        $.post('/request/auth-reset',{
            email: $('#email').val()
        }, function(result){
            if(result.status === 0){
                loader(0)
            }else if(result.status === 1){
                location.replace(window.location.origin);
            }
            $('#notification-box > span').text(result.message)
        }).fail(function () {
            $('#notification-box > span').text('Maaf sistem sedang ada ada gangguan');
        });
        $('#notification-box').delay(200).fadeIn('slow').css('display', 'flex');

    })
}

function register() {
    $('form').submit(function (e) {
        e.preventDefault();


        $.post('/request/auth-register',{
            name: $('#name').val(),
            username: $('#username').val(),
            storename: $('#storename').val(),
            email: $('#email').val(),
            password: $('#password').val(),
            password2: $('#password2').val()
        }, function(result){
            if(result.status === 0 || result.status === 2){
                loader(0)
            }else{
                location.replace(window.location.origin);
            }
            $('#notification-box > span').text(result.message)
        }).fail(function () {
            $('#notification-box > span').text('Maaf sistem sedang ada ada gangguan');
        });

        $('#notification-box').delay(200).css('display','inherit').fadeIn('slow');

    })
}

$('#notif-close').click(function () {
    $(this).parent().delay(200).fadeOut('slow');
    loader(0);
});
