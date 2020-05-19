function plotLineChart(plot_params,plotID) {
    
    console.log(plot_params['x_axis']);
    var ctx = document.getElementById(plotID);
    var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: plot_params['x_axis'],
        datasets: [
        { 
            label:plotID + ' Value',
            data: plot_params['y_axis'],
            fill: false,
            'borderColor': "rgb(75,192,192)",
            'lineTension': 0.1,
        }
        ]
    },
    options: {
        scales: {
            xAxes: [{
                ticks: {
                    display: false
                }
            }]
        }
    }
    });
}

