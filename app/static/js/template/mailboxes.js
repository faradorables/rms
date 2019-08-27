/**
 * Developed by ION Developer Team
 * URL : https://ION.id
 */

 $(document).ready(function () {

});

$('a._toggle').click(function(){
  let _target = $(this).data('target');
  console.log($('#' + _target));
  $('#' + _target).collapse('toggle');
  $('#' + _target).on('hidden.bs.collapse', function () {
    $('#' + _target).css('display', 'none');
  }).on('show.bs.collapse', function () {
    $('#' + _target).css('display', 'flex');
  })
})

$('._check').on('change click', function(e){
  e.stopPropagation();
})

function open_mail(){
  console.log('Open Email')
}

function open_important(){
  console.log('Open Important');
  event.stopPropagation();
}

function open_starred(){
  console.log('Open Starred');
  event.stopPropagation();
}

function open_trash(){
  console.log('Open Trash');
  event.stopPropagation();
}
