let tasks = Array.from(document.getElementsByClassName('task-item'));

let now = new Date();
let nowWithoutTime = new Date(year=now.getFullYear(), month=now.getMonth(), day=now.getDate());
let nowWithoutTimePlus1Day = new Date(year=now.getFullYear(), month=now.getMonth(), day=now.getDate() + 1)
for (let i=0; i < tasks.length; i++) {
    let deadline = tasks[i].getAttribute('deadline');
    let deadlineYear = deadline.split(':')[0]
    let deadlineMonth = deadline.split(':')[1]
    let deadlineDay = deadline.split(':')[2]
    if (deadline.length < 5) {
        continue
    }
    let deadlineDate = new Date(year=deadlineYear, month=deadlineMonth-1, day=deadlineDay);
    if (deadlineDate.getTime() == nowWithoutTime.getTime()) {
        tasks[i].style.backgroundColor = 'rgba(255, 0, 0, 0.4)';
        tasks[i].innerHTML = tasks[i].innerHTML + '<div class="fire-icon-container"><i class="ri-fire-line"></i></div>'
    }
    else if (deadlineDate.getTime() == nowWithoutTimePlus1Day.getTime()) {
        tasks[i].style.backgroundColor = 'rgba(255, 0, 0, 0.4)';
        tasks[i].innerHTML = tasks[i].innerHTML + '<div class="fire-icon-container"><i class="ri-fire-line"></i></div>'     
    }
    else if (deadlineDate < nowWithoutTime) {
        tasks[i].style.backgroundColor = 'rgba(255, 0, 0, 0.4)';
        tasks[i].innerHTML = tasks[i].innerHTML + '<div class="fire-icon-container"><i class="ri-fire-line"></i></div>'        
    }
}
