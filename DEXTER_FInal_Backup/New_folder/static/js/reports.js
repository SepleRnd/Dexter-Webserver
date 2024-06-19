document.getElementById('downloadBtn').addEventListener('click', function() {
    const reportType = document.getElementById('reportType').value;
    let fileName;
    let fileContent;

    switch (reportType) {
        case 'daily':
            fileName = 'daily_report.txt';
            fileContent = 'This is the daily report content.';
            break;
        case 'monthly':
            fileName = 'monthly_report.txt';
            fileContent = 'This is the monthly report content.';
            break;
        case 'quarterly':
            fileName = 'quarterly_report.txt';
            fileContent = 'This is the quarterly report content.';
            break;
        default:
            fileName = 'report.txt';
            fileContent = 'This is the default report content.';
    }

    // Create an anchor element                                                                                                                       
    const a = document.createElement('a');
    // Set the file name
    a.download = fileName;
    // Create a blob object
    const blob = new Blob([fileContent], { type: 'text/plain' });
    // Create an object URL
    a.href = URL.createObjectURL(blob);
    // Append the anchor to the body
    document.body.appendChild(a);
    // Trigger the download
    a.click();
    // Remove the anchor from the document
    document.body.removeChild(a);
});
