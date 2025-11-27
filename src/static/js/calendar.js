const contentWrapper = document.querySelector('#scrollWrapper');
const scrollLeftButton = document.getElementById('btnPrev');
const scrollRightButton = document.getElementById('btnNext');

let currentIndex = 1;

function dropDownCalendarMark(event, message) {
  event.preventDefault();
  const element = document.getElementById('calendarModalContent');
  element.innerHTML = message;
  element.parentElement.classList.toggle('show')

}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}


// Функция для создания нового контента
function createNewContent() {
    const newContent = document.createElement('div');
    newContent.classList.add('month');
    newContent.innerHTML = '<div class="calendar-wrapper"></div>';
    return newContent;
}

function createCalendarMark(deadlinesOnCurrentDate, deadlinesCount, deadline) {
    let message = ''
    const pretty_deadline = deadline.toLocaleString('ru-RU', {year: 'numeric', month: 'long', day: 'numeric'});
    const count = String(deadlinesOnCurrentDate[deadlinesCount]['count'])
    if (['11', '12', '13', '14'].includes(count)) {
        message = `<h2>На ${pretty_deadline} у вас запланировано ${deadlinesOnCurrentDate[deadlinesCount]['count']} задач в категории ${deadlinesOnCurrentDate[deadlinesCount]['category'].toLowerCase()}</h2>`
    }
    else if (count.endsWith('1')) {
        message = `<h2>На ${pretty_deadline} у вас запланирована ${deadlinesOnCurrentDate[deadlinesCount]['count']} задача в категории ${deadlinesOnCurrentDate[deadlinesCount]['category'].toLowerCase()}</h2>`
    }
    else if (count.endsWith('2') || count.endsWith('3') || count.endsWith('4')) {
        message = `<h2>На ${pretty_deadline} у вас запланированы ${deadlinesOnCurrentDate[deadlinesCount]['count']} задачи в категории ${deadlinesOnCurrentDate[deadlinesCount]['category'].toLowerCase()}</h2>`
    }
    else {
        message = `<h2>На ${pretty_deadline} у вас запланировано ${deadlinesOnCurrentDate[deadlinesCount]['count']} задач в категории ${deadlinesOnCurrentDate[deadlinesCount]['category'].toLowerCase()}</h2>`
    }
    escapedMessage = escapeHtml(message);
    const html = `
        <button onclick="dropDownCalendarMark(event, '${escapedMessage}')" class="calendar-mark-button" id="" title="У вас запланировано следующее количество задач в категории ${deadlinesOnCurrentDate[deadlinesCount]['category']}: ${deadlinesOnCurrentDate[deadlinesCount]['count']}" style="background-color: ${deadlinesOnCurrentDate[deadlinesCount]['color']};"></button>

    `
    return html

}


var Cal = function() {
    //Сохраняем идентификатор div
    // Дни недели с понедельника
    this.DaysOfWeek = [
        'Пн',
        'Вт',
        'Ср',
        'Чтв',
        'Птн',
        'Суб',
        'Вск'
    ];

    this.deadlines = calendar_data;
    // Месяцы начиная с января
    this.Months =['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    //Устанавливаем текущий месяц, год

    this.getDeadlinesByDate = (year, month, day) => {
        if (String(month).length < 2) {
            month = '0' + month
        }
        if (String(day).length < 2) {
            day = '0' + day
        }
        return this.deadlines[year + '.' + month + '.' + day]
    }

    var d = new Date();
    this.currMonth = d.getMonth();
    this.currYear = d.getFullYear();
    this.currDay = d.getDate();
    };
    // Переход к следующему месяцу
    Cal.prototype.nextMonth = function(element) {
        if ( this.currMonth == 11 ) {
            this.currMonth = 0;
            this.currYear = this.currYear + 1;
        }
        else {
            this.currMonth = this.currMonth + 1;
        }
        this.showMonth(this.currYear, this.currMonth, element);
    };
    // Переход к предыдущему месяцу
    Cal.prototype.previousMonth = function(element) {
        if ( this.currMonth == 0 ) {
            this.currMonth = 11;
            this.currYear = this.currYear - 1;
        }
        else {
            this.currMonth = this.currMonth - 1;
        }
        this.showMonth(this.currYear, this.currMonth, element);
    };
    // Показать месяц (год, месяц)
    Cal.prototype.showMonth = function(y, m, element) {
        var d = new Date()
        // Первый день недели в выбранном месяце 
        , firstDayOfMonth = new Date(y, m, 7).getDay()
        // Последний день выбранного месяца
        , lastDateOfMonth =  new Date(y, m+1, 0).getDate()
        // Последний день предыдущего месяца
        , lastDayOfLastMonth = m == 0 ? new Date(y-1, 11, 0).getDate() : new Date(y, m, 0).getDate();
        var html = '<table>';
        // Запись выбранного месяца и года
        html += '<thead><tr>';
        html += '<td colspan="7">' + this.Months[m] + ' ' + y + '</td>';
        html += '</tr></thead>';
        // заголовок дней недели
        html += '<tr class="days">';
        for(var i=0; i < this.DaysOfWeek.length;i++) {
            html += '<td>' + this.DaysOfWeek[i] + '</td>';
        }
        html += '</tr>';
        // Записываем дни
        var i=1;
        do {
            var dow = new Date(y, m, i).getDay();
            // Начать новую строку в понедельник
            if ( dow == 1 ) {
            html += '<tr>';
            }
            // Если первый день недели не понедельник показать последние дни предыдущего месяца
            else if ( i == 1 ) {
            html += '<tr>';
            var k = lastDayOfLastMonth - firstDayOfMonth+1;
            for(var j=0; j < firstDayOfMonth; j++) {
                html += '<td class="not-current">' + k + '</td>';
                k++;
            }
            }
            // Записываем текущий день в цикл
            var chk = new Date();
            var chkY = chk.getFullYear();
            var chkM = chk.getMonth();
            if (chkY == y && chkM == m && i == this.currDay) {
                
                let deadlinesOnCurrentDate = this.getDeadlinesByDate(this.currYear, this.currMonth+1, i)
                let deadlinesHtml = ''
                if (deadlinesOnCurrentDate) {
                    for(let deadlinesCount=0; deadlinesCount < deadlinesOnCurrentDate.length; deadlinesCount++) {
                        deadlinesHtml += createCalendarMark(deadlinesOnCurrentDate, deadlinesCount, new Date(this.currYear, this.currMonth, i));
                    }                    
                }
                html += '<td class="normal"">' + i + '<div class="deadlines-container">' + deadlinesHtml + '</div>' + '</td>';

            }
            else {
                let deadlinesOnCurrentDate = this.getDeadlinesByDate(this.currYear, this.currMonth+1, i)
                let deadlinesHtml = ''
                if (deadlinesOnCurrentDate) {
                    for(let deadlinesCount=0; deadlinesCount < deadlinesOnCurrentDate.length; deadlinesCount++) {
                        deadlinesHtml += createCalendarMark(deadlinesOnCurrentDate, deadlinesCount, new Date(this.currYear, this.currMonth, i));
                    }                    
                }

                html += '<td class="normal"">' + i + '<div class="deadlines-container">' + deadlinesHtml + '</div>' + '</td>';
                     
            }
            // закрыть строку в воскресенье
            if ( dow == 0 ) {
                html += '</tr>';
            }
            // Если последний день месяца не воскресенье, показать первые дни следующего месяца
            else if ( i == lastDateOfMonth ) {
                var k=1;
                for(dow; dow < 7; dow++) {
                    html += '<td class="not-current">' + k + '</td>';
                    k++;
                }
            }
            i++;
        }while(i <= lastDateOfMonth);
        // Конец таблицы
        html += '</table>';
        // Записываем HTML в div
        element.innerHTML = html;
    }
window.onload = function() {
    // Начать календарь
    let divs = document.getElementsByClassName('calendar-wrapper');
    let calendar = new Cal();
    let calendarNext = new Cal();
    let calendarPrev = new Cal();
    calendar.showMonth(calendar.currYear, calendar.currMonth, divs[6]);
    
    for (let i = 0; i < 6; i++) {
        calendarNext.nextMonth(divs[7+i]);
    }

    for (let i = 0; i < 6; i++) {
        calendarPrev.previousMonth(divs[5-i]);
    }

    let currentIndex = 6;

    function renderNextYear () {
        for (let i = 0; i < 12; i++) {
            let content = createNewContent();
            contentWrapper.appendChild(content);
            let months = document.getElementsByClassName('calendar-wrapper');
            calendarNext.nextMonth(months[months.length - 1]);

        }

    }

    function renderPrevYear () {
        for (let i = 0; i < 12; i++) {
            let content = createNewContent();
            contentWrapper.prepend(content);
            let months = document.getElementsByClassName('calendar-wrapper');
            calendarPrev.previousMonth(months[0]);
            

        }
        currentIndex = 12;
    }

    
    // Скролл вправо
    scrollRightButton.addEventListener('click', () => {
        // Увеличиваем индекс текущего контента
        currentIndex = (currentIndex + 1) % divs.length;
        console.log(currentIndex);
        contentWrapper.style.transform = `translateX(-${currentIndex * 500}px)`;
        contentWrapper.addEventListener('transitionend', () => {
            if (contentWrapper.style.transform == `translateX(-${500 * divs.length - 500}px)`) {
                renderNextYear();
                divs = document.getElementsByClassName('calendar-wrapper');
            }
        }, { once: true });
    });

    // Скролл влево
    scrollLeftButton.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + divs.length) % divs.length;
        console.log(currentIndex);
        contentWrapper.style.transition = 'transform 0.5s ease-in-out';
        contentWrapper.style.transform = `translateX(-${currentIndex * 500}px)`;
        contentWrapper.addEventListener('transitionend', () => {
            if (contentWrapper.style.transform == 'translateX(0px)') {
                renderPrevYear();
                console.log(currentIndex);
                divs = document.getElementsByClassName('calendar-wrapper');
                contentWrapper.style.transition = 'none';
                contentWrapper.style.transform = 'translateX(-6000px)';    
            }
        }, { once: true });
    });

    
}