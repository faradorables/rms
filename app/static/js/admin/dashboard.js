function graph(){
  _loading(0);

      let ctx_line = document.getElementById("myChart_line");
      let data = {
          labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
          datasets: [{
              label: 'Total User',
              data:[12,13,13,12,11,15,16,17,17,19,18,20],
              // data: [e.january, e.february, e.march, e.april, e.may, e.june, e.july, e.august, e.september, e.october, e.november, e.december],
              backgroundColor: 'transparent',
              borderColor: 'rgba(58, 43, 112, 1)',
              borderWidth: 2
          }, {
              label: 'New User',
              data: [12, 1, 0, 0, 0, 4, 1, 1, 0, 2, 0, 1],
              backgroundColor: 'transparent',
              borderColor: 'rgba(58, 43, 112, .5)',
              borderWidth: 2
          }]
      };
      let myLineChart = new Chart(ctx_line, {
      type: 'line',
      data: data,
      options: {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero:true
                  }
              }]
          }
      }
      });
      let ctx_line_1 = document.getElementById("myChart_line_1");
      let data_1 = {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
          datasets: [{
              label: 'Floating Money',
              data: [10,
                12,
                11,
                15,
                18,
                25,
                23,
                23,
                26,
                27,
                29,
                30],
              backgroundColor: 'rgba(58, 43, 112, .5)',
              borderColor: 'rgba(58, 43, 112, 1)',
              borderWidth: 2
          }]
      };
      let myLineChart_1 = new Chart(ctx_line_1, {
      type: 'line',
      data: data_1,
      options: {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero:true
                  }
              }]
          }
      }
      });
      var ctx = document.getElementById("myChart");
      var myChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Agt", "Sep", "Oct", "Nov", "Des"],
            datasets: [{
                label: 'Pulsa',
                data: [14, 21, 5, 7, 5, 8],
                backgroundColor: 'rgba(58, 43, 112, .5)',
                borderWidth: 1
            }, {
                label: 'PLN',
                data: [12,13,14,11,10,9,17,16,16,15,18,17],
                // data: [e.january, e.february, e.march, e.april, e.may, e.june, e.july, e.august, e.september, e.october, e.november, e.december],
                backgroundColor: 'rgba(58, 43, 112, 1)',
                borderWidth: 1
            },{
                label: 'OBU',
                data: [12, 93, 23, 31, 30,45],
                backgroundColor: 'rgba(23, 23, 80, 1)',
                borderWidth: 1
            }]
          },
          options: {
              scales: {
                  yAxes: [{
                      ticks: {
                          beginAtZero:true
                      },
                  }],
                  xAxes: [{
                      ticks: {
                          beginAtZero:true
                      },
                  }]
              }
          }
      });
}
