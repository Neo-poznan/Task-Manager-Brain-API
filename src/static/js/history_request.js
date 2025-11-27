function openHistory() {
    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;
    if (fromDate && toDate) {
        window.open(`/history/?from_date=${fromDate}&to_date=${toDate}`)
    }
    
}

