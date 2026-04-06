const STORAGE_KEY = 'claritinote_jobs';

function loadJobs() {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
}

function saveJobs(jobs) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
}

function removeJob(jobId) {
    saveJobs(loadJobs().filter(j => j.id !== jobId));
    document.getElementById('card-' + jobId).remove();
    if (loadJobs().length === 0) {
        document.getElementById('results-section').style.display = 'none';
    }
}

function createCard(job) {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.id = 'card-' + job.id;
    card.innerHTML = `
        <div class="card-header">
            <span class="filename" title="${job.name}">${job.name}</span>
            <div style="display:flex;align-items:center;gap:10px;">
                <span id="badge-${job.id}" class="badge-pending">
                    <div class="spinner"></div> Processing…
                </span>
                <button type="button" class="btn-dismiss" title="Dismiss">×</button>
            </div>
        </div>
        <div id="body-${job.id}"></div>
    `;
    card.querySelector('.btn-dismiss').addEventListener('click', () => removeJob(job.id));
    return card;
}

function markFinished(jobId, status, content) {
    const badge = document.getElementById('badge-' + jobId);
    const done = status === 'done';
    badge.className = done ? 'badge-done' : 'badge-error';
    badge.innerHTML = done
        ? '<i class="fas fa-check mr-1"></i> Done'
        : '<i class="fas fa-exclamation-circle mr-1"></i> Error';

    const body = document.getElementById('body-' + jobId);
    if (done) {
        const ta = document.createElement('textarea');
        ta.readOnly = true;
        ta.value = content;
        body.appendChild(ta);
    } else {
        const p = document.createElement('p');
        p.style.cssText = 'color:#e74c3c;font-size:14px;margin:0';
        p.textContent = content;
        body.appendChild(p);
    }

    const jobs = loadJobs();
    const job = jobs.find(j => j.id === jobId);
    if (job) {
        job.status = status;
        job.result = content;
        saveJobs(jobs);
    }
}

function connectSSE(jobId) {
    const source = new EventSource(`/stream/${jobId}`);
    source.onmessage = (e) => {
        const data = JSON.parse(e.data);
        source.close();
        markFinished(jobId, data.status, data.result);
    };
    source.onerror = () => source.close();
}

function renderAll() {
    const jobs = loadJobs();
    if (jobs.length === 0) return;

    document.getElementById('results-section').style.display = 'block';
    const container = document.getElementById('cards-container');
    for (const job of jobs) {
        container.appendChild(createCard(job));
        if (job.status === 'pending') connectSSE(job.id);
        else markFinished(job.id, job.status, job.result);
    }
}

function initClaritiNote() {
    const el = document.getElementById('page-bootstrap');
    const boot = el ? JSON.parse(el.textContent.trim()) : {};
    const newJobId = boot.job_id;
    const newJobName = boot.job_name;

    if (newJobId) {
        const jobs = loadJobs();
        jobs.unshift({ id: newJobId, name: newJobName, status: 'pending', result: null });
        saveJobs(jobs);
    }

    renderAll();
}

initClaritiNote();
