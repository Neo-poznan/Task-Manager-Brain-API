const data = {
  labels: chart_data.categories,
  datasets: [{
    label: 'Задач в категории',
    data: chart_data.counts,
    backgroundColor: chart_data.colors,
    hoverOffset: 4
  }]
};



const ctx = document.getElementById('chart');

const config = {
    type: 'doughnut',
    data: data,
    options: { elements: { arc: { borderColor: "rgb(15, 15, 15)" } } }

}

new Chart(ctx, config);