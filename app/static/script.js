document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const filenameDisplay = document.getElementById('filename-display');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('results-section');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    let selectedFile = null;

    // Drag & Drop handlers
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        selectedFile = file;
        filenameDisplay.textContent = `Selected: ${file.name}`;
        fileInfo.classList.remove('hidden');
        dropZone.classList.add('hidden');
    }

    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));

            btn.classList.add('active');
            document.getElementById(target).classList.remove('hidden');
        });
    });

    // Analysis trigger
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Reset UI
        fileInfo.classList.add('hidden');
        loader.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();

            // Render results
            document.getElementById('summary-content').innerHTML = marked.parse(data.summary);
            document.getElementById('balance-content').innerHTML = marked.parse(data.balance_sheet);
            document.getElementById('tax-content').innerHTML = marked.parse(data.tax_return);

            loader.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            resultsSection.classList.add('fade-in');

        } catch (error) {
            console.error(error);
            alert('Error analyzing file. Please check console.');
            loader.classList.add('hidden');
            fileInfo.classList.remove('hidden');
        }
    });
});
