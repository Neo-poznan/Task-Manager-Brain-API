const contentWrapper = document.querySelector('.statistics-wrapper');
const contents = document.querySelectorAll('.content');
const nextButton = document.getElementById('btnNext');
const prevButton = document.getElementById('btnPrev');

let currentIndex = 0;

nextButton.addEventListener('click', () => {
    // Увеличиваем индекс текущего контента
    currentIndex = (currentIndex + 1) % contents.length;

    // Смещаем wrapper влево на ширину одного контента
    contentWrapper.style.transform = `translateX(-${currentIndex * 500}px)`;
});

prevButton.addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + contents.length) % contents.length;
    contentWrapper.style.transform = `translateX(-${currentIndex * 500}px)`;
});

const countUserTasksInCategoriesCTX = document.getElementById('countUserTasksInCategoriesChart');

const countUserTasksInCategoriesChartData = {
  labels: countUserTasksInCategories.labels,
  datasets: [{
    label: 'Задач в категории',
    data: countUserTasksInCategories.data,
    backgroundColor: countUserTasksInCategories.colors,
    hoverOffset: 4
  }]
};

const countUserTasksInCategoriesConfig = {
    type: 'doughnut',
    data: countUserTasksInCategoriesChartData,
    options: { elements: { arc: { borderColor: "rgb(15, 15, 15)" } } }

}

new Chart(countUserTasksInCategoriesCTX, countUserTasksInCategoriesConfig);

const userAccuracyByCategoriesCTX = document.getElementById('userAccuracyByCategoriesChart')

const userAccuracyByCategoriesChartData = {
    labels: userAccuracyByCategories.labels,
    datasets: [{
        label: 'Точность вашего планирования',
        barThickness: 13,
        maxBarThickness: 20,
        minBarLength: 2,
        data: userAccuracyByCategories.data,
        backgroundColor: userAccuracyByCategories.colors,

    }],
};


const userAccuracyByCategoriesConfig = {
  type: 'bar',
  data: userAccuracyByCategoriesChartData,
  options: {
        indexAxis: 'x',
        responsive: true,
        scales: {
            x: {
                grid: {
                    color: 'gray'
                }
            },
            y: {
                grid: {
                    color: 'gray' 
                }
            }
        }
    }
};


new Chart(userAccuracyByCategoriesCTX, userAccuracyByCategoriesConfig);

const userSuccessRateByCategoriesCTX = document.getElementById('userSuccessRateByCategoriesChart')

const userSuccessRateByCategoriesChartData = {
    labels: userSuccessRateByCategories.labels,
    datasets: [{
        label: 'Успешно выполненные задачи',
        barThickness: 13,
        maxBarThickness: 20,
        minBarLength: 2,
        data: userSuccessRateByCategories.data,
        backgroundColor: userSuccessRateByCategories.colors,

    }],
};

const userSuccessRateByCategoriesConfig = {
  type: 'bar',
  data: userSuccessRateByCategoriesChartData,
  options: {
        indexAxis: 'x',
        responsive: true,
        scales: {
            x: {
                grid: {
                    color: 'gray'
                }
            },
            y: {
                grid: {
                    color: 'gray' 
                }
            }
        }
    }
};

new Chart(userSuccessRateByCategoriesCTX, userSuccessRateByCategoriesConfig);

const countUserTasksByWeekdaysCTX = document.getElementById('countUserTasksByWeekdaysChart');


const countUserTasksByWeekdaysChartData = {
  labels: countUserTasksByWeekdays.labels,
  datasets: [{
    label: 'Задачи по дням недели',
    data: countUserTasksByWeekdays.data,
    backgroundColor: 'rgba(56, 248, 255, 0.4)',
    hoverOffset: 4,
    barThickness: 13,
    maxBarThickness: 20,
    minBarLength: 2,
  }],

};

const countUserTasksByWeekdaysConfig = {
    type: 'bar',
    data: countUserTasksByWeekdaysChartData,
    options: {
      indexAxis: 'x',
      responsive: true,
      scales: {
          x: {
              grid: {
                  color: 'gray'
              }
          },
          y: {
              grid: {
                  color: 'gray' 
              }
          }
      }
  }

}

new Chart(countUserTasksByWeekdaysCTX, countUserTasksByWeekdaysConfig)

const countUserSuccessfulPlannedTasksByCategoriesCTX = document.getElementById('countUserSuccessfulPlannedTasksByCategoriesChart');

const countUserSuccessfulPlannedTasksByCategoriesChartData = {
  labels: countUserSuccessfulPlannedTasksByCategories.labels,
  datasets: [{
    label: 'Задачи, в которых запланированное время совпадает с временем выполнения',
    data: countUserSuccessfulPlannedTasksByCategories.data,
    backgroundColor: countUserSuccessfulPlannedTasksByCategories.colors,
    hoverOffset: 4,
    barThickness: 13,
    maxBarThickness: 20,
    minBarLength: 2,

  }],

};

const countUserSuccessfulPlannedTasksByCategoriesConfig = {
    type: 'bar',
    data: countUserSuccessfulPlannedTasksByCategoriesChartData,
    options: {
      indexAxis: 'x',
      responsive: true,
      scales: {
          x: {
              grid: {
                  color: 'gray'
              }
          },
          y: {
              grid: {
                  color: 'gray' 
              }
          }
      }
  }

}

new Chart(countUserSuccessfulPlannedTasksByCategoriesCTX, countUserSuccessfulPlannedTasksByCategoriesConfig)

const commonUserAccuracyCTX = document.getElementById('commonUserAccuracyChart')

const commonUserAccuracyChartData = {
  datasets: [{
    label: 'Точность планирования',
    data: commonUserAccuracy.data,
    backgroundColor: commonUserAccuracy.colors,
    hoverOffset: 4
  }]
};

const commonUserAccuracyConfig = {
    type: 'doughnut',
    data: commonUserAccuracyChartData,
    options: { 
      elements: { 
        arc: { borderColor: "rgb(15, 15, 15)" } },
        plugins: {
            tooltip: {
                bodyFont: {
                    size: 9
                }
            }
        }
    }
}

new Chart(commonUserAccuracyCTX, commonUserAccuracyConfig)

const commonUserSuccessRateCTX = document.getElementById('commonUserSuccessRateChart')

const commonUserSuccessRateChartData = {
  datasets: [{
    label: 'Успешные задачи',
    data: commonUserSuccessRate.data,
    backgroundColor: commonUserSuccessRate.colors,
    hoverOffset: 4
  }]
};

const commonUserSuccessRateConfig = {
    type: 'doughnut',
    data: commonUserSuccessRateChartData,
    options: { 
      elements: { 
        arc: { borderColor: "rgb(15, 15, 15)" } },
        plugins: {
            tooltip: {
                bodyFont: {
                    size: 9
                }
            }
        }
    }
}

new Chart(commonUserSuccessRateCTX, commonUserSuccessRateConfig)


const commonCountUserSuccessfulPlannedTasksCTX = document.getElementById('commonCountUserSuccessfulPlannedTasksChart')

const commonCountUserSuccessfulPlannedTasksChartData = {
  datasets: [{
    label: 'Правильно спланировано',
    data: commonCountUserSuccessfulPlannedTasks.data,
    backgroundColor: commonCountUserSuccessfulPlannedTasks.colors,
    hoverOffset: 4
  }]
};

const commonCountUserSuccessfulPlannedTasksConfig = {
    type: 'doughnut',
    data: commonCountUserSuccessfulPlannedTasksChartData,
    options: { 
      elements: { 
        arc: { borderColor: "rgb(15, 15, 15)" } },
        plugins: {
            tooltip: {
                bodyFont: {
                    size: 9
                }
            }
        }
    }
}

new Chart(commonCountUserSuccessfulPlannedTasksCTX, commonCountUserSuccessfulPlannedTasksConfig)

function getQueryParam(name){
   if(name=(new RegExp('[?&]'+encodeURIComponent(name)+'=([^&]*)')).exec(location.search))
      return decodeURIComponent(name[1]);
}

function showDates() {
    const from_date = new Date(getQueryParam('from_date')).toLocaleString('ru-RU', {
        year: 'numeric', month: 'long', day: 'numeric'
    }); 
    const to_date = new Date(getQueryParam('to_date')).toLocaleString('ru-RU', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    document.getElementById('historyDates').innerText = from_date + ' - ' + to_date;
}

function shareHistory() {
    const from_date = getQueryParam('from_date');
    const to_date = getQueryParam('to_date');
    const url = window.location
    let modal = document.getElementById('modalShareHistory');    
    fetch(`/history/share/?from_date=${from_date}&to_date=${to_date}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'X-CSRFToken': csrf_token // Установка CSRF-токена в заголовок
            },
    })
    .then(response => response.json())
    .then(response => {
        animateHeightChange(modal, () => {
            modal.innerHTML = `
                <div class="skip-button-container">
                    <button id="modalShareHistorySkip" class="skip-button" onclick="closeModalShareHistory()"><i class="ri-close-large-line close-icon" id="modalShareHistoryCloseIcon"></i></button>
                </div>
                <div class="modal-content" style="width: 600px;">
                    <h1 class="share-history-info">История сохранена по этой ссылке:</h1>
                    <p class="share-history-info" id="readyLink">${url.protocol}://${url.host}/history/share/?key=${response.key}</p>
                    <button id="copyLinkButton" onclick="copyLink(event)" class="copy-link-button"><i class="ri-file-copy-line"></i></button>
                </div>
            `
        })
    })
    .catch(error => {
        modal.innerHTML = `
            <div class="skip-button-container">
                <button id="modalShareHistorySkip" class="skip-button" onclick="closeModalShareHistory()"><i class="ri-close-large-line close-icon" id="modalShareHistoryCloseIcon"></i></button>
            </div>
            <div class="modal-content">            
                <h1 class="share-history-info">${error}</h1>          
            </div>      
        
        `     
    })
}

function copyLink(e) {
    e.preventDefault()
    const linkElement = document.getElementById('readyLink');
    navigator.clipboard.writeText(linkElement.innerHTML)
    .then(() => {
        e.target.parentElement.classList.add('copied');
        e.target.parentElement.innerHTML = '<p style="color: white;">Скопировано<i class="ri-check-line" style="color: green;"></i></p>';
        e.target.parentElement.style.transition = 'all 0.3s ease';
    })
    .catch(error => {
        console.log(error);
    })
}


function animateHeightChange(element, changeContentCallback) {
    // 1. Запоминаем текущую высоту
    const startWidth = element.offsetWidth;

    // 2. Устанавливаем фиксированную высоту, чтобы transition сработал
    element.style.width = startWidth + 'px';

    // 3. Меняем содержимое
    changeContentCallback();

    // 4. Измеряем новую высоту
    console.log(startWidth);
    const endWidth = element.children[1].style.width;
    console.log(element.children[1]);
    console.log(endWidth);

    // 5. Запускаем переход к новой высоте
    requestAnimationFrame(() => {
        element.style.transition = 'width 0.5s ease';
        element.style.width = Number(endWidth.slice(0, 3)) + 140 + 'px';
    });

    // 6. После окончания анимации сбрасываем height в auto
    element.addEventListener('transitionend', function handler() {
        element.style.width = 'auto';
        element.style.transition = '';
        element.removeEventListener('transitionend', handler);
    });
}


