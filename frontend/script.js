document.addEventListener('DOMContentLoaded', () => {
    const commentForm = document.getElementById('commentForm');
    const commentInput = document.getElementById('commentInput');
    const fetchSampleBtn = document.getElementById('fetchSampleBtn');
    const commentTableBody = document.getElementById('commentTableBody');
    const commentCount = document.getElementById('commentCount');
    const loading = document.getElementById('loading');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');

    // UI elements for stats
    const statTotal = document.getElementById('statTotal');
    const statPositive = document.getElementById('statPositive');
    const statHigh = document.getElementById('statHigh');
    const statAvg = document.getElementById('statAvg');

    // Filter elements
    const searchInput = document.getElementById('searchInput');
    const filterSentiment = document.getElementById('filterSentiment');
    const filterPriority = document.getElementById('filterPriority');
    const resetFilters = document.getElementById('resetFilters');

    let allComments = []; // Keep a local copy for filtering

    const instaForm = document.getElementById('instaForm');
    const instaUrl = document.getElementById('instaUrl');

    // Initial load
    refreshData();

    // Auto-refresh data every 30 seconds for "real-time" feeling
    setInterval(refreshData, 30000);

    // Instagram form handler
    instaForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Extra check if it's disabled in settings
        if (localStorage.getItem('instaSyncEnabled') === 'false') {
            window.showMagicToast('Instagram integration is currently disabled in settings.', 'error');
            return;
        }

        const url = instaUrl.value.trim();
        if (!url) return;

        showLoading(true);
        try {
            const response = await fetch('/api/import/instagram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ post_url: url })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Import failed');

            let message = data.message;
            if (data.total_fetched > 0) {
                const speedNote = data.fetch_time ? ` in ${data.fetch_time}s` : '';
                message += `\n(Fetched ${data.total_fetched} total comments${speedNote})`;
            }
            window.showMagicToast(message, 'success');
            instaUrl.value = '';

            // Clear filters to ensure the new comments are visible
            searchInput.value = '';
            filterSentiment.value = '';
            filterPriority.value = '';

            await refreshData();
        } catch (error) {
            console.error('Instagram Import Error:', error);
            window.showMagicToast('Error: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    });

    // Initial load
    refreshData();

    async function refreshData() {
        await fetchComments();
        await fetchAnalytics();
    }

    // Submit handler
    commentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = commentInput.value.trim();
        if (!text) return;

        showLoading(true);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment_text: text })
            });

            if (!response.ok) throw new Error('Submission failed');

            // Success response
            commentInput.value = '';

            // Clear filters to ensure the new comment is visible
            searchInput.value = '';
            filterSentiment.value = '';
            filterPriority.value = '';

            await refreshData();
        } catch (error) {
            console.error('Error submitting comment:', error);
            window.showMagicToast('Failed to analyze comment. Please check if the backend is running.', 'error');
        } finally {
            showLoading(false);
        }
    });

    // API Call demo
    fetchSampleBtn.addEventListener('click', async () => {
        const samples = [
            "the fabric is so soft omg!! love it 😍✨",
            "abe o bevakuf, stop sending spam emails!! 😡",
            "kinda expensive for this quality tbh. could be better. 😕",
            "delivery was late again.. pls fix it. 🚨",
            "awesome update!! ❤️ the new features r fire 🔥",
            "hey i cant login into my account. pls assist asap. 🆘",
            "Hello idiot! Worst experience ever!! 🤮",
            "i want this product to be comfortable and soft",
            "I want this product to be more soft and comfortable to use, it's a bit rough right now..",
            "i want this product to have better comfort for long use",
            "Found a glitch in the checkout page... it just crashes 😭"
        ];
        commentInput.value = samples[Math.floor(Math.random() * samples.length)];
    });

    async function fetchComments() {
        try {
            const response = await fetch('/api/comments');
            if (!response.ok) throw new Error('Fetch failed');

            allComments = await response.json();
            applyFilters();
        } catch (error) {
            console.error('Error fetching comments:', error);
        }
    }

    async function fetchAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            if (!response.ok) throw new Error('Analytics failed');

            const stats = await response.json();
            statTotal.textContent = stats.total;
            statPositive.textContent = stats.sentiments.Positive || 0;
            statHigh.textContent = stats.priorities.High || 0;

            const pos = stats.sentiments.Positive || 0;
            const neg = stats.sentiments.Negative || 0;
            const total = pos + neg + (stats.sentiments.Neutral || 0);
            if (total > 0) {
                const score = ((pos * 1 + neg * -1) / total).toFixed(2);
                statAvg.textContent = score > 0 ? `+${score}` : score;
            } else {
                statAvg.textContent = "--";
            }
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    }

    function applyFilters() {
        if (!allComments) {
            allComments = [];
        }

        const search = (searchInput.value || "").toLowerCase();
        const sentiment = filterSentiment.value;
        const priority = filterPriority.value;

        const filtered = allComments.filter(c => {
            const commentStr = (c.comment_text || "").toLowerCase();
            const matchesSearch = !search || commentStr.includes(search);
            const matchesSentiment = !sentiment || c.sentiment === sentiment;
            const matchesPriority = !priority || c.priority === priority;
            return matchesSearch && matchesSentiment && matchesPriority;
        });

        renderTable(filtered);
        commentCount.textContent = `${filtered.length} Results`;
    }

    // Filter event listeners
    searchInput.addEventListener('input', applyFilters);
    filterSentiment.addEventListener('change', applyFilters);
    filterPriority.addEventListener('change', applyFilters);
    resetFilters.addEventListener('click', () => {
        searchInput.value = '';
        filterSentiment.value = '';
        filterPriority.value = '';
        applyFilters();
    });

    function renderTable(comments) {
        commentTableBody.innerHTML = '';

        if (comments.length === 0) {
            commentTableBody.innerHTML = `<tr><td colspan="7" class="text-center py-5" style="color: white; font-family: 'Times New Roman', serif;">No matching records found.</td></tr>`;
            return;
        }

        comments.forEach(c => {
            const row = document.createElement('tr');

            const priorityClass = `priority-${c.priority.toLowerCase()}`;
            const sentimentClass = `sentiment-${c.sentiment.toLowerCase()}`;

            const date = new Date(c.timestamp);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            row.innerHTML = `
                <td>
                    <div class="fw-medium mb-1">${c.comment_text}</div>
                    <div class="small text-info opacity-75 d-md-none">ID: #${c.id}</div>
                </td>
                <td class="small text-light opacity-75">@${c.user_handle}</td>
                <td><span class="badge-category">${c.category}</span></td>
                <td><span class="badge-sentiment ${sentimentClass}"></span>${c.sentiment}</td>
                <td><span class="badge badge-priority ${priorityClass}">${c.priority}</span></td>
                <td class="timestamp-text">${formattedDate}</td>
                <td class="text-center">
                    <button class="btn-delete" onclick="deleteComment(${c.id})" title="Delete entry">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            `;

            commentTableBody.appendChild(row);
        });
    }

    window.deleteComment = async (id) => {
        if (!confirm('Are you sure you want to delete this feedback?')) return;

        try {
            const response = await fetch(`/api/comments/${id}`, { method: 'DELETE' });
            if (response.ok) {
                await refreshData();
            }
        } catch (error) {
            console.error('Delete error:', error);
        }
    };

    exportCsvBtn.addEventListener('click', () => {
        if (allComments.length === 0) return;

        const headers = ["ID", "Comment", "Category", "Sentiment", "Priority", "Timestamp"];
        const rows = allComments.map(c => [
            c.id,
            `"${c.comment_text.replace(/"/g, '""')}"`,
            c.category,
            c.sentiment,
            c.priority,
            c.timestamp
        ]);

        const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", "feedback_data.csv");
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    clearAllBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete ALL feedback? This action cannot be undone.')) return;

        try {
            const response = await fetch('/api/comments/clear', { method: 'DELETE' });
            if (response.ok) {
                await refreshData();
                window.showMagicToast('Database cleared successfully.', 'success');
            }
        } catch (error) {
            console.error('Clear error:', error);
            window.showMagicToast('Failed to clear database.', 'error');
        }
    });

    let loadingInterval = null;
    const loadingText = document.getElementById('loadingText');
    const loadingStepsContainer = document.getElementById('loadingStepsContainer');

    function showLoading(active) {
        loading.classList.toggle('d-none', !active);
        
        if (active) {
            if (loadingText) loadingText.textContent = "Processing...";
            if (loadingStepsContainer) loadingStepsContainer.innerHTML = '';
            
            const statuses = [
                "[*] Booting extraction engine...",
                "[+] Bypassing strict API rate limits...",
                "[>] Resolving Media ID for target URL...",
                "[+] Fetching pure comment payloads...",
                "[*] Scrubbing strings & stripping emojis...",
                "[>] Initializing NLP Sentiment Model...",
                "[*] Running polarity heuristics...",
                "[+] Scanning for profanity triggers...",
                "[>] Calculating priority weights...",
                "[*] Clustering custom AI categories...",
                "[+] Verifying data hash integrity...",
                "[*] Committing to local SQL cluster..."
            ];
            let index = 0;
            
            loadingInterval = setInterval(() => {
                if (!loadingStepsContainer) return;
                
                // Complete previous step
                if (index > 0 && index <= statuses.length) {
                    const prevStep = document.getElementById(`step-${index - 1}`);
                    if (prevStep) {
                        prevStep.classList.remove('active');
                        prevStep.classList.add('completed');
                        let oldText = statuses[index - 1].substring(4);
                        prevStep.innerHTML = `<i class="fas fa-check-circle"></i> [OK] ${oldText}`;
                    }
                }
                
                // Add new active step
                if (index < statuses.length) {
                    const newStep = document.createElement('div');
                    newStep.id = `step-${index}`;
                    newStep.className = `step-item active`;
                    newStep.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${statuses[index]}`;
                    loadingStepsContainer.appendChild(newStep);
                    index++;
                } else {
                    clearInterval(loadingInterval);
                    loadingInterval = null;
                }
            }, 300); // Super fast hacker speed
        } else {
            if (loadingInterval) {
                clearInterval(loadingInterval);
                loadingInterval = null;
            }
            if (loadingText) loadingText.textContent = "Analyzed at last ✓";
            
            if (loadingStepsContainer) {
                // Complete whatever step was active
                const activeStep = loadingStepsContainer.querySelector('.step-item.active');
                if (activeStep) {
                    activeStep.classList.remove('active');
                    activeStep.classList.add('completed');
                    let rawText = activeStep.innerText.trim();
                    if (rawText.startsWith('[') && rawText.indexOf(']') === 2) {
                        rawText = "[OK] " + rawText.substring(4); // replaces [*] with [OK]
                    } else if (!rawText.startsWith('[OK]')) {
                        rawText = "[OK] " + rawText;
                    }
                    activeStep.innerHTML = `<i class="fas fa-check-circle"></i> ${rawText}`;
                }
                
                // Add final victory piece
                const finalStep = document.createElement('div');
                finalStep.className = `step-item completed`;
                finalStep.innerHTML = `<i class="fas fa-check-double"></i> Analyzed at last`;
                loadingStepsContainer.appendChild(finalStep);
            }
        }
    }

    // --- Settings Management ---
    const toggleInstaSync = document.getElementById('toggleInstaSync');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const instaTab = document.getElementById('insta-tab');

    // Load settings from localStorage
    function loadSettings() {
        const instaEnabled = localStorage.getItem('instaSyncEnabled') !== 'false'; // Default to true
        toggleInstaSync.checked = instaEnabled;
        applySettings(instaEnabled);
    }

    function applySettings(enabled) {
        if (enabled) {
            instaTab.classList.remove('disabled-tab');
            instaTab.removeAttribute('title');
        } else {
            instaTab.classList.add('disabled-tab');
            instaTab.setAttribute('title', 'Instagram integration is disabled in settings');

            // If the user was on the insta tab, switch back to manual
            if (instaTab.classList.contains('active')) {
                const manualTab = new bootstrap.Tab(document.getElementById('manual-tab'));
                manualTab.show();
            }
        }
    }

    saveSettingsBtn.addEventListener('click', () => {
        const isEnabled = toggleInstaSync.checked;
        localStorage.setItem('instaSyncEnabled', isEnabled);
        applySettings(isEnabled);

        // Show a small toast or alert
        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 end-0 p-3';
        toast.style.zIndex = '1055';
        toast.innerHTML = `
            <div class="glass-card p-3 border-info animate-up">
                <i class="fas fa-check-circle text-info me-2"></i> Settings saved successfully!
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    });

    // Initialize settings
    loadSettings();

    // --- Magic Notifications System (Replaces native alerts) ---
    window.showMagicToast = function(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = 'position-fixed top-0 end-0 p-4 mt-4 me-4 animate-up';
        toast.style.zIndex = '9999';
        
        const icon = type === 'success' ? '<i class="fas fa-check-circle text-success fs-3"></i>' : '<i class="fas fa-exclamation-triangle text-danger fs-3"></i>';
        const borderColor = type === 'success' ? 'border-success' : 'border-danger';
        const titleText = type === 'success' ? 'Task Completed' : 'Attention';

        toast.innerHTML = `
            <div class="glass-card p-3 ${borderColor} shadow-lg d-flex align-items-center gap-3" style="min-width: 320px; border-left-width: 4px;">
                ${icon}
                <div>
                    <h6 class="mb-1 fw-bold text-white text-uppercase tracking-wider" style="letter-spacing: 1px;">${titleText}</h6>
                    <p class="mb-0 small text-light opacity-75">${message.replace(/\n/g, '<br>')}</p>
                </div>
                <button type="button" class="btn-close btn-close-white ms-auto align-self-start" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        document.body.appendChild(toast);
        
        // Auto-remove gracefully
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-20px)';
                toast.style.transition = 'all 0.4s ease';
                setTimeout(() => toast.remove(), 400);
            }
        }, 6000);
    };
});
