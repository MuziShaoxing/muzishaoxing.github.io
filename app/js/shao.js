
        (function() {
            "use strict";
            if (typeof XLSX === 'undefined') { alert('Excel库加载失败'); return; }

            const fileInput = document.getElementById('fileInput');
            const attendanceInput = document.getElementById('attendanceInput');
            const orderFileTrigger = document.getElementById('orderFileTrigger');
            const attFileTrigger = document.getElementById('attFileTrigger');
            const analyzeBtn = document.getElementById('analyzeBtn');
            const exportReportBtn = document.getElementById('exportReportBtn');
            const resultTableHead = document.querySelector('#resultTable thead');
            const resultTableBody = document.querySelector('#resultTable tbody');
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            const previewArea = document.getElementById('previewArea');
            const previewContainer = document.getElementById('previewContainer');
            const previewTable = document.getElementById('previewTable');
            const togglePreviewBtn = document.getElementById('togglePreviewBtn');
            const mappingConfigBtn = document.getElementById('mappingConfigBtn');
            const mappingModal = document.getElementById('mappingModal');
            const mapOrderRider = document.getElementById('mapOrderRider');
            const mapOrderTime = document.getElementById('mapOrderTime');
            const mapOrderStore = document.getElementById('mapOrderStore');
            const mapOrderBlock = document.getElementById('mapOrderBlock');
            const mapOrderStatus = document.getElementById('mapOrderStatus');
            const mapAttRider = document.getElementById('mapAttRider');
            const mapAttStart = document.getElementById('mapAttStart');
            const mapAttEnd = document.getElementById('mapAttEnd');
            const mapAttStatus = document.getElementById('mapAttStatus');
            const mapAttRiderType = document.getElementById('mapAttRiderType');
            const applyMappingBtn = document.getElementById('applyMappingBtn');
            const closeModalBtn = document.getElementById('closeModalBtn');
            const viewToggleGroup = document.getElementById('viewToggleGroup');
            const riderFilterCompact = document.getElementById('riderFilterCompact');
            const riderSearchInput = document.getElementById('riderSearchInput');
            const riderDropdown = document.getElementById('riderDropdown');
            const riderClearBtn = document.getElementById('riderClearBtn');
            const statusIcon = document.getElementById('statusIcon');
            const statusMessage = document.getElementById('statusMessage');
            const statusBadge = document.getElementById('statusBadge');
            const scrollWrapper = document.getElementById('tableScrollWrapper');
            const heatmapLegend = document.getElementById('heatmapLegend');
            const blockLegend = document.getElementById('blockLegend');
            const typeLegend = document.getElementById('typeLegend');
            const appContainer = document.querySelector('.app-container');
            const typeGranToggle = document.getElementById('typeGranToggle');
            const typeGranText = document.getElementById('typeGranText');

            let workbookData = null,
                attendanceWorkbook = null,
                riderShiftsMap = new Map(),
                riderTypeMap = new Map();
            let structHalfHour = null,
                structHour = null,
                blockStats = null,
                typeStatsHalf = null,
                typeStatsHour = null,
                blockTimeStatsHalf = null,
                blockTimeStatsHour = null;
            let currentView = 'half';
            let typeViewGran = 'half';
            let previewVisible = true,
                storeName = '';
            let currentMapping = {
                orderRider: '配送员姓名',
                orderTime: '订单配送完成时间',
                orderStore: '',
                orderBlock: '',
                orderStatus: '',
                attRider: '考勤骑手.配送员姓名',
                attStart: '配送班次.班次开始时间',
                attEnd: '配送班次.班次结束时间',
                attStatus: '班次状态（1：取消；0：正常）',
                attRiderType: '骑手类型'
            };
            let selectedRiders = new Set();
            let allRiderNames = [];

            // 拖拽滚动
            let isDragging = false,
                startX = 0,
                startY = 0,
                scrollLeft = 0,
                scrollTop = 0;

            function applyScrollLimits() {
                const maxLeft = scrollWrapper.scrollWidth - scrollWrapper.clientWidth;
                const maxTop = scrollWrapper.scrollHeight - scrollWrapper.clientHeight;
                scrollWrapper.scrollLeft = Math.max(0, Math.min(scrollWrapper.scrollLeft, maxLeft));
                scrollWrapper.scrollTop = Math.max(0, Math.min(scrollWrapper.scrollTop, maxTop));
            }

            function onDragStart(pageX, pageY) {
                isDragging = true;
                scrollWrapper.style.cursor = 'grabbing';
                startX = pageX - scrollWrapper.offsetLeft;
                startY = pageY - scrollWrapper.offsetTop;
                scrollLeft = scrollWrapper.scrollLeft;
                scrollTop = scrollWrapper.scrollTop;
            }

            function onDragMove(pageX, pageY) {
                if (!isDragging) return;
                const dx = pageX - scrollWrapper.offsetLeft - startX;
                const dy = pageY - scrollWrapper.offsetTop - startY;
                let newLeft = scrollLeft - dx * 1.5;
                let newTop = scrollTop - dy * 1.5;
                const maxLeft = scrollWrapper.scrollWidth - scrollWrapper.clientWidth;
                const maxTop = scrollWrapper.scrollHeight - scrollWrapper.clientHeight;
                newLeft = Math.max(0, Math.min(newLeft, maxLeft));
                newTop = Math.max(0, Math.min(newTop, maxTop));
                scrollWrapper.scrollLeft = newLeft;
                scrollWrapper.scrollTop = newTop;
            }

            function onDragEnd() {
                isDragging = false;
                scrollWrapper.style.cursor = 'grab';
                applyScrollLimits();
            }
            scrollWrapper.addEventListener('mousedown', (e) => {
                if (e.target.closest(
                        'button, select, input, .view-option, .rider-search-input, .rider-clear-btn')) return;
                e.preventDefault();
                onDragStart(e.pageX, e.pageY);
            });
            window.addEventListener('mousemove', (e) => { if (!isDragging) return;
                e.preventDefault();
                onDragMove(e.pageX, e.pageY); });
            window.addEventListener('mouseup', onDragEnd);
            scrollWrapper.addEventListener('touchstart', (e) => {
                if (e.target.closest(
                        'button, select, input, .view-option, .rider-search-input, .rider-clear-btn')) return;
                if (e.touches.length !== 1) return;
                e.preventDefault();
                onDragStart(e.touches[0].pageX, e.touches[0].pageY);
            }, { passive: false });
            scrollWrapper.addEventListener('touchmove', (e) => { if (!isDragging) return;
                e.preventDefault();
                onDragMove(e.touches[0].pageX, e.touches[0].pageY); }, { passive: false });
            scrollWrapper.addEventListener('touchend', onDragEnd);
            scrollWrapper.addEventListener('touchcancel', onDragEnd);
            window.addEventListener('mouseleave', () => { if (isDragging) onDragEnd(); });
            document.addEventListener('touchcancel', () => { if (isDragging) onDragEnd(); });
            scrollWrapper.addEventListener('scroll', () => { if (!isDragging) applyScrollLimits(); });

            orderFileTrigger.onclick = () => fileInput.click();
            attFileTrigger.onclick = () => attendanceInput.click();

            function isDeliveredOrder(row, statusCol) {
                if (!statusCol) return true;
                return String(row[statusCol] || '').trim().includes('妥投');
            }

            function parseTimeToDate(v) {
                if (!v && v !== 0) return null;
                if (v instanceof Date && !isNaN(v)) return v;
                let s = String(v).trim();
                if (s === '') return null;
                if (!isNaN(s) && s > 40000 && s < 60000) { let d = new Date((s - 25569) * 86400000); if (!isNaN(d))
                        return d; }
                let d = new Date(s);
                if (!isNaN(d)) return d;
                let m = s.match(/(\d{1,2}):(\d{1,2})/); if (m) { let t = new Date();
                    t.setHours(+m[1], +m[2], 0, 0); return t; }
                return null;
            }

            function loadExcel(file) {
                return new Promise((resolve, reject) => {
                    const r = new FileReader();
                    r.onload = e => {
                        try {
                            const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array',
                                cellDates: true, defval: '' });
                            const sh = wb.Sheets[wb.SheetNames[0]];
                            const rows = XLSX.utils.sheet_to_json(sh, { header: 1, defval: '' });
                            if (!rows || rows.length < 2) reject('无数据');
                            const h = rows[0].map(c => String(c || '').trim());
                            const data = rows.slice(1).filter(r => r.some(c => c !== undefined && c !== '' && c !==
                                null)).map(r => { let o = {};
                                h.forEach((c, i) => o[c] = r[i]); return o; });
                            resolve({ columns: h, data });
                        } catch (e) { reject(e); }
                    };
                    r.onerror = () => reject('读取失败');
                    r.readAsArrayBuffer(file);
                });
            }

            function parseAttendance(mapping) {
                const shiftsMap = new Map();
                riderTypeMap.clear();
                if (!attendanceWorkbook?.data) return shiftsMap;
                const { attRider, attStart, attEnd, attStatus, attRiderType } = mapping;
                if (!attRider || !attStart || !attEnd) return shiftsMap;
                for (let row of attendanceWorkbook.data) {
                    let name = String(row[attRider] || '').trim();
                    if (!name) continue;
                    let start = parseTimeToDate(row[attStart]),
                        end = parseTimeToDate(row[attEnd]);
                    if (start && end) {
                        let status = attStatus ? row[attStatus] : 0;
                        if ((typeof status === 'number' ? status : parseInt(status) || 0) === 0) {
                            if (!shiftsMap.has(name)) shiftsMap.set(name, []);
                            shiftsMap.get(name).push({ startHour: start.getHours(), startMin: start.getMinutes(),
                                endHour: end.getHours(), endMin: end.getMinutes() });
                        }
                    }
                    if (attRiderType && !riderTypeMap.has(name)) {
                        let typeVal = String(row[attRiderType] || '').trim();
                        riderTypeMap.set(name, typeVal || '未分类');
                    }
                }
                for (let name of shiftsMap.keys())
                if (!riderTypeMap.has(name)) riderTypeMap.set(name, '未分类');
                return shiftsMap;
            }

            function populateSelect(sel, cols, def) {
                sel.innerHTML = '';
                if (!cols?.length) { sel.innerHTML = '<option>-- 暂无列 --</option>'; return; }
                cols.forEach(c => sel.add(new Option(c, c)));
                sel.value = def && cols.includes(def) ? def : cols[0];
            }

            function getHeatColor(v, min, max) {
                if (max === min || max <= 0) return '#b9f6ca';
                let t = (v - min) / (max - min);
                return `rgb(${Math.floor(34 + 205*t)}, ${Math.floor(197 - 129*t)}, ${Math.floor(94 - 26*t)})`;
            }

            function isWorking(slot, shifts) {
                if (!shifts?.length) return true;
                let ss = slot.startHour * 60 + slot.startMin,
                    se = slot.endHour * 60 + slot.endMin;
                return shifts.some(s => (s.startHour * 60 + s.startMin) < se && (s.endHour * 60 + s.endMin) > ss);
            }

            function getBlockSortKey(blockName) {
                const name = String(blockName).trim();
                let layerOrder = 4;
                if (name.includes('内环')) layerOrder = 0;
                else if (name.includes('外环')) layerOrder = 1;
                else if (name.includes('环外')) layerOrder = 2;
                else if (name.includes('跨区')) layerOrder = 3;
                const dirKeywords = ['中', '东', '西', '南', '北', '特', '跨', '接驳'];
                let dirOrder = 8;
                for (let i = 0; i < dirKeywords.length; i++)
                if (name.includes(dirKeywords[i])) { dirOrder = i; break; }
                let numOrder = 99;
                const arabicMatch = name.match(/[1-5]/);
                if (arabicMatch) numOrder = parseInt(arabicMatch[0]);
                else { const cnNumMap = { '一': 1, '二': 2, '三': 3, '四': 4, '五': 5 }; for (let [cn, val] of Object.entries(
                        cnNumMap))
                    if (name.includes(cn)) { numOrder = val; break; } }
                return layerOrder * 10000 + dirOrder * 100 + numOrder;
            }

            function computeBlockTimeStats(gran, riderFilterSet) {
                if (!workbookData || !currentMapping.orderBlock || !currentMapping.orderTime || !currentMapping
                    .orderRider) return null;
                const data = workbookData.data,
                    blockCol = currentMapping.orderBlock,
                    timeCol = currentMapping.orderTime,
                    riderCol = currentMapping.orderRider,
                    sCol = currentMapping.orderStatus;
                const freq = gran === '半小时' ? 30 : 60;
                let slotMap = new Map();
                for (let row of data) {
                    if (!isDeliveredOrder(row, sCol)) continue;
                    let dt = parseTimeToDate(row[timeCol]); if (!dt) continue;
                    let mins = dt.getHours() * 60 + dt.getMinutes();
                    let start = Math.floor(mins / freq) * freq;
                    if (!slotMap.has(start)) { let sh = Math.floor(start / 60),
                            sm = start % 60,
                            eh = Math.floor((start + freq) / 60),
                            em = (start + freq) % 60;
                        slotMap.set(start, { sortKey: start, startHour: sh, startMin: sm, endHour: eh, endMin: em }); }
                }
                let slots = Array.from(slotMap.values()).sort((a, b) => a.sortKey - b.sortKey);
                if (!slots.length) return null;
                const blockOrderSet = new Map(),
                    blockSlotOrders = {},
                    blockTotalOrders = {};
                for (let row of data) {
                    if (!isDeliveredOrder(row, sCol)) continue;
                    let riderName = String(row[riderCol] || '').trim();
                    if (riderFilterSet && riderFilterSet.size > 0 && !riderFilterSet.has(riderName)) continue;
                    let block = String(row[blockCol] || '').trim(); if (!block) continue;
                    let dt = parseTimeToDate(row[timeCol]); if (!dt) continue;
                    let mins = dt.getHours() * 60 + dt.getMinutes();
                    let start = Math.floor(mins / freq) * freq;
                    let idx = slots.findIndex(s => s.sortKey === start); if (idx === -1) continue;
                    if (!blockOrderSet.has(block)) { blockOrderSet.set(block, true);
                        blockSlotOrders[block] = Array(slots.length).fill(0);
                        blockTotalOrders[block] = 0; }
                    blockSlotOrders[block][idx]++;
                    blockTotalOrders[block]++;
                }
                const blocks = Array.from(blockOrderSet.keys()).sort((a, b) => getBlockSortKey(a) - getBlockSortKey(b));
                if (blocks.length === 0) return null;
                const blockRows = blocks.map(block => ({ block, orders: blockSlotOrders[block], total: blockTotalOrders[
                        block] }));
                return { slots, blocks, blockRows };
            }

            function computeTypeStats(gran, riderFilterSet) {
                if (!workbookData || !currentMapping.orderRider || !currentMapping.orderTime) return null;
                const data = workbookData.data,
                    tCol = currentMapping.orderTime,
                    rCol = currentMapping.orderRider,
                    sCol = currentMapping.orderStatus;
                const freq = gran === '半小时' ? 30 : 60;
                let slotMap = new Map();
                for (let row of data) { if (!isDeliveredOrder(row, sCol)) continue; let dt = parseTimeToDate(row[tCol]); if (!dt)
                        continue; let mins = dt.getHours() * 60 + dt.getMinutes(); let start = Math.floor(mins / freq) *
                        freq; if (!slotMap.has(start)) { let sh = Math.floor(start / 60),
                            sm = start % 60,
                            eh = Math.floor((start + freq) / 60),
                            em = (start + freq) % 60;
                        slotMap.set(start, { sortKey: start, startHour: sh, startMin: sm, endHour: eh, endMin: em }); } }
                let slots = Array.from(slotMap.values()).sort((a, b) => a.sortKey - b.sortKey);
                if (!slots.length) return null;
                const typeOrderSet = new Map(),
                    typeSlotOrders = {},
                    typeSlotRidersSet = {},
                    typeTotalOrders = {},
                    typeTotalRidersSet = new Map();
                for (let row of data) {
                    if (!isDeliveredOrder(row, sCol)) continue;
                    let riderName = String(row[rCol] || '').trim(); if (!riderName) continue;
                    if (riderFilterSet && riderFilterSet.size > 0 && !riderFilterSet.has(riderName)) continue;
                    let dt = parseTimeToDate(row[tCol]); if (!dt) continue;
                    let mins = dt.getHours() * 60 + dt.getMinutes();
                    let start = Math.floor(mins / freq) * freq;
                    let idx = slots.findIndex(s => s.sortKey === start); if (idx === -1) continue;
                    let riderType = riderTypeMap.get(riderName) || '未分类';
                    if (!typeOrderSet.has(riderType)) { typeOrderSet.set(riderType, true);
                        typeSlotOrders[riderType] = Array(slots.length).fill(0);
                        typeSlotRidersSet[riderType] = Array(slots.length).fill().map(() => new Set());
                        typeTotalOrders[riderType] = 0;
                        typeTotalRidersSet.set(riderType, new Set()); }
                    typeSlotOrders[riderType][idx]++;
                    typeSlotRidersSet[riderType][idx].add(riderName);
                    typeTotalOrders[riderType]++;
                    typeTotalRidersSet.get(riderType).add(riderName);
                }
                // 【修改2】按总单量降序排列骑手类型
                const types = Array.from(typeOrderSet.keys()).sort((a, b) => typeTotalOrders[b] - typeTotalOrders[a]);
                if (types.length === 0) return null;
                const typeRows = types.map(type => { const orders = typeSlotOrders[type]; const ridersPerSlot =
                        typeSlotRidersSet[type].map(s => s.size); const eff = orders.map((o, i) => ridersPerSlot[i] ? Math
                        .round((o / ridersPerSlot[i]) * 10) / 10 : 0); return { type, orders, ridersPerSlot, eff,
                        totalOrders: typeTotalOrders[type], totalRiders: typeTotalRidersSet.get(type).size }; });
                return { slots, types, typeRows };
            }

            function renderTypeTable(typeStats, gran, blockTimeStats) {
                if (!typeStats || !typeStats.typeRows.length) {
                    resultTableHead.innerHTML = '<tr><th>提示</th></tr>';
                    resultTableBody.innerHTML =
                        '<tr><td>请上传考勤并在字段映射中配置"骑手类型"列，且确保订单数据有效</td></tr>';
                    return;
                }
                const { slots, typeRows } = typeStats;
                let h = '<tr><th>骑手类型 / 区块</th>';
                slots.forEach(s => h +=
                    `<th><span class="slot-start">${s.startHour.toString().padStart(2,'0')}:${s.startMin.toString().padStart(2,'0')}</span><span class="slot-end">↓${s.endHour.toString().padStart(2,'0')}:${s.endMin.toString().padStart(2,'0')}</span></th>`
                    );
                h += '<th>总单量</th><th>总人数</th></tr>';
                resultTableHead.innerHTML = h;

                let body = '';
                // 【修改1】每行独立热力范围 - 骑手类型部分
                typeRows.forEach(r => {
                    body +=
                    `<tr><td style="font-weight:700;background-color:#f0fdf4;">${r.type}</td>`;
                    const rowOrders = r.orders;
                    const rowMin = Math.min(0, ...rowOrders);
                    const rowMax = Math.max(1, ...rowOrders);
                    r.orders.forEach(v => {
                        const bg = getHeatColor(v, rowMin, rowMax);
                        body +=
                        `<td style="background:${bg};font-weight:600;">${v}</td>`;
                    });
                    body +=
                        `<td style="font-weight:700;background:#f0fdf4;">${r.totalOrders}</td><td style="background:#f0fdf4;">${r.totalRiders}</td></tr>`;
                });

                if (blockTimeStats && blockTimeStats.blockRows.length > 0) {
                    const { blockRows } = blockTimeStats;
                    let sep = `<td style="background:#cbd5e6;">────────</td>` + slots.map(() =>
                        '<td style="background:#cbd5e6;">─</td>').join('') +
                        '<td style="background:#cbd5e6;">─</td><td style="background:#cbd5e6;">─</td>';
                    body += `<tr class="separator-row">${sep}</tr>`;

                    // 【修改2】区块按总单量降序排列
                    const sortedBlockRows = [...blockRows].sort((a, b) => b.total - a.total);
                    // 【修改1】每行独立热力范围 - 区块部分
                    sortedBlockRows.forEach(r => {
                        body +=
                        `<tr><td style="font-weight:700;background:#eef2ff;">📦 ${r.block}</td>`;
                        const brOrders = r.orders;
                        const brMin = Math.min(0, ...brOrders);
                        const brMax = Math.max(1, ...brOrders);
                        r.orders.forEach(v => {
                            const bg = getHeatColor(v, brMin, brMax);
                            body +=
                            `<td style="background:${bg};font-weight:600;">${v}</td>`;
                        });
                        body +=
                            `<td style="font-weight:700;background:#eef2ff;">${r.total}</td><td style="background:#eef2ff;">—</td></tr>`;
                    });
                }
                resultTableBody.innerHTML = body;
                updateStatus('骑手类型对比', `${typeRows.length}种类型 · ${typeRows.reduce((s,r)=>s+r.totalOrders,0)}单`,
                'success');
            }

            function setActiveView(view) {
                if (view === 'type') { selectedRiders.clear();
                    riderSearchInput.value = ''; if (riderDropdown) riderDropdown.classList.remove('show'); if (currentView ===
                        'half' || currentView === 'hour') typeViewGran = currentView; }
                if (view !== currentView) { scrollWrapper.scrollLeft = 0;
                    scrollWrapper.scrollTop = 0; }
                currentView = view;
                document.querySelectorAll('.view-option').forEach(o => o.classList.remove('active'));
                const activeOption = document.querySelector(`.view-option[data-view="${view}"]`);
                if (activeOption) activeOption.classList.add('active');
                heatmapLegend.style.display = (view === 'half' || view === 'hour') ? 'flex' : 'none';
                blockLegend.style.display = (view === 'block') ? 'flex' : 'none';
                typeLegend.style.display = (view === 'type') ? 'flex' : 'none';
                // 【修改3】管理type-view-active和block-view-active class
                appContainer.classList.remove('block-view-active', 'type-view-active');
                if (view === 'block') appContainer.classList.add('block-view-active');
                if (view === 'type') appContainer.classList.add('type-view-active');
                if (view === 'type') { riderFilterCompact.style.display = 'none';
                    typeGranToggle.style.display = 'inline-flex';
                    typeGranText.value = typeViewGran === 'half' ? '点击切换小时' : '点击切换半小时'; } else {
                    typeGranToggle.style.display = 'none'; const hasData = structHalfHour || structHour || typeStatsHalf ||
                        typeStatsHour;
                    riderFilterCompact.style.display = hasData ? 'inline-flex' : 'none';
                }
                renderCurrentView();
            }
            viewToggleGroup.addEventListener('click', (e) => { const opt = e.target.closest('.view-option'); if (!opt)
                    return; const view = opt.dataset.view; if (view === currentView) return;
                setActiveView(view); });
            typeGranToggle.addEventListener('click', () => { if (currentView !== 'type') return;
                typeViewGran = typeViewGran === 'half' ? 'hour' : 'half';
                typeGranText.value = typeViewGran === 'half' ? '点击切换小时' : '点击切换半小时';
                renderCurrentView(); });

            function renderRiderDropdown() {
                const filter = riderSearchInput.value.toLowerCase().trim();
                const filtered = filter ? allRiderNames.filter(n => n.toLowerCase().includes(filter)) :
                allRiderNames;
                if (filtered.length === 0) { riderDropdown.innerHTML =
                    '<div class="rider-no-result">😕 无匹配骑手</div>'; return; }
                riderDropdown.innerHTML = filtered.map(name => { const checked = selectedRiders.has(name); return (
                        `<div class="rider-option${checked?' checked':''}" data-value="${name}"><span class="rider-checkbox">✓</span>${name}</div>`
                        ); }).join('');
            }

            function openRiderDropdown() { riderDropdown.classList.add('show');
                renderRiderDropdown(); }

            function closeRiderDropdown() { riderDropdown.classList.remove('show'); }
            riderSearchInput.addEventListener('focus', openRiderDropdown);
            riderSearchInput.addEventListener('input', openRiderDropdown);
            riderSearchInput.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeRiderDropdown();
                    riderSearchInput.blur(); } });
            riderDropdown.addEventListener('click', (e) => { e.stopPropagation(); const opt = e.target.closest(
                    '.rider-option'); if (!opt) return; const value = opt.dataset.value;
                selectedRiders.has(value) ? selectedRiders.delete(value) : selectedRiders.add(value);
                renderRiderDropdown();
                riderSearchInput.focus();
                renderCurrentView(); });
            // 【修改4】清空按钮点击后不触发下拉
riderClearBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    selectedRiders.clear();
    riderSearchInput.value = '';
    renderRiderDropdown();
    renderCurrentView();
    // 移除 focus()，避免移动端弹出键盘
    riderDropdown.classList.remove('show');
});
            document.addEventListener('click', (e) => { if (!riderFilterCompact.contains(e.target))
                closeRiderDropdown(); });

            function updateRiderFilterUI(names) {
                allRiderNames = names || [];
                if (!allRiderNames.length) { riderFilterCompact.style.display = 'none'; return; }
                if (currentView !== 'type') riderFilterCompact.style.display = 'inline-flex';
                selectedRiders.clear();
                riderSearchInput.value = '';
                renderRiderDropdown();
            }

            function renderCurrentView() {
                if (currentView === 'block') {
                    if (blockStats) { let displayRiders = selectedRiders.size > 0 ? blockStats.riderRows.filter(r =>
                            selectedRiders.has(r.rider)) : blockStats.riderRows;
                        renderBlockTable({ ...blockStats, riderRows: displayRiders }); } else {
                        resultTableHead.innerHTML = '<tr><th>提示</th></tr>';
                        resultTableBody.innerHTML = '<tr><td>请在字段映射中设置"区块列"并上传订单</td></tr>';
                    }
                } else if (currentView === 'type') {
                    const typeStats = typeViewGran === 'half' ? typeStatsHalf : typeStatsHour;
                    const blockTimeStats = typeViewGran === 'half' ? blockTimeStatsHalf : blockTimeStatsHour;
                    if (typeStats) renderTypeTable(typeStats, typeViewGran, blockTimeStats);
                    else {
                        resultTableHead.innerHTML = '<tr><th>提示</th></tr>';
                        resultTableBody.innerHTML =
                            '<tr><td>请上传考勤并配置"骑手类型"映射列，然后点击"开始分析"</td></tr>';
                    }
                } else {
                    const struct = currentView === 'half' ? structHalfHour : structHour;
                    if (!struct?.riderDisplay) return;
                    let filtered = selectedRiders.size > 0 ? struct.riderDisplay.filter(r => selectedRiders.has(r
                        .rider)) : struct.riderDisplay;
                    renderTableWithHeatmap({ ...struct, riderDisplay: filtered }, riderShiftsMap);
                    updateStatus(`${currentView==='half'?'半小时':'小时'}视图`,
                        `${filtered.length}位骑手 · ${struct.rawOrders.reduce((a,b)=>a+b,0)}单`, 'success');
                }
            }

            function updateStatus(msg, badge, type = 'info') {
                statusMessage.textContent = msg;
                statusIcon.textContent = type === 'success' ? '✅' : (type === 'error' ? '❌' : (type === 'warning' ?
                    '⚠️' : 'ℹ️'));
                statusBadge.textContent = badge || '';
                statusBadge.style.display = badge ? 'inline' : 'none';
            }

            async function applyMappingAndAnalyze() {
                if (!workbookData) { updateStatus('请上传订单', '', 'error'); return; }
                currentMapping = { orderRider: mapOrderRider.value, orderTime: mapOrderTime.value, orderStore: mapOrderStore
                        .value, orderBlock: mapOrderBlock.value, orderStatus: mapOrderStatus.value, attRider: mapAttRider
                        .value, attStart: mapAttStart.value, attEnd: mapAttEnd.value, attStatus: mapAttStatus.value,
                    attRiderType: mapAttRiderType.value };
                if (!currentMapping.orderTime || !currentMapping.orderRider) { updateStatus('缺少必要映射', '', 'error');
                    return; }
                mappingModal.style.display = 'none';
                storeName = extractStoreName();
                riderShiftsMap = (attendanceWorkbook && currentMapping.attRider) ? parseAttendance(currentMapping) : new Map();
                await performAnalysis();
            }
            async function performAnalysis() {
                if (!workbookData?.data?.length || !currentMapping.orderTime || !currentMapping.orderRider) { updateStatus(
                        '请上传并配置映射', '', 'error'); return; }
                analyzeBtn.disabled = true;
                exportReportBtn.disabled = true;
                progressBar.style.display = 'block';
                progressFill.style.width = '30%';
                updateStatus('分析中...', '', 'info');
                try {
                    structHalfHour = analyzeData('半小时');
                    structHour = analyzeData('小时');
                    if (currentMapping.orderBlock) blockStats = computeBlockStats(); else blockStats = null;
                    typeStatsHalf = computeTypeStats('半小时', null);
                    typeStatsHour = computeTypeStats('小时', null);
                    blockTimeStatsHalf = computeBlockTimeStats('半小时', null);
                    blockTimeStatsHour = computeBlockTimeStats('小时', null);
                    updateRiderFilterUI(structHalfHour.riderDisplay.map(r => r.rider));
                    progressFill.style.width = '100%';
                    setTimeout(() => progressBar.style.display = 'none', 300);
                    exportReportBtn.disabled = false;
                    renderCurrentView();
                } catch (e) { updateStatus(`失败: ${e.message}`, '', 'error');
                    progressBar.style.display = 'none';
                    resultTableHead.innerHTML = '<tr><th>错误</th></tr>';
                    resultTableBody.innerHTML = `<tr><td>${e.message}</td></tr>`; } finally { analyzeBtn.disabled = false;
                    progressFill.style.width = '0%'; }
            }

            function analyzeData(gran) {
                const data = workbookData.data,
                    tCol = currentMapping.orderTime,
                    rCol = currentMapping.orderRider,
                    sCol = currentMapping.orderStatus;
                let valid = [];
                for (let r of data) { if (!isDeliveredOrder(r, sCol)) continue; let rider = r[rCol]; if (!rider && rider !== 0)
                        continue; let dt = parseTimeToDate(r[tCol]); if (!dt) continue;
                    valid.push({ rider: String(rider).trim(), time: dt }); }
                if (!valid.length) throw new Error('无有效数据（请检查订单状态是否为"妥投"');
                const freq = gran === '半小时' ? 30 : 60;
                let slotMap = new Map();
                valid.forEach(v => { let mins = v.time.getHours() * 60 + v.time.getMinutes(); let start = Math.floor(mins /
                        freq) * freq; if (!slotMap.has(start)) { let sh = Math.floor(start / 60),
                            sm = start % 60,
                            eh = Math.floor((start + freq) / 60),
                            em = (start + freq) % 60;
                        slotMap.set(start, { sortKey: start, startHour: sh, startMin: sm, endHour: eh, endMin: em }); } });
                let slots = Array.from(slotMap.values()).sort((a, b) => a.sortKey - b.sortKey);
                if (!slots.length) throw new Error('时段为空');
                let slotOrders = Array(slots.length).fill(0),
                    slotRiderSet = Array(slots.length).fill().map(() => new Set()),
                    riderMap = new Map();
                valid.forEach(v => { let mins = v.time.getHours() * 60 + v.time.getMinutes(); let start = Math.floor(mins /
                        freq) * freq; let idx = slots.findIndex(s => s.sortKey === start); if (idx === -1) return; if (!riderMap
                        .has(v.rider)) riderMap.set(v.rider, new Map()); let rm = riderMap.get(v.rider);
                    rm.set(idx, (rm.get(idx) || 0) + 1);
                    slotOrders[idx]++;
                    slotRiderSet[idx].add(v.rider); });
                let slotRiders = slotRiderSet.map(s => s.size),
                    eff = slotOrders.map((o, i) => slotRiders[i] ? o / slotRiders[i] : 0);
                let riderRows = [];
                for (let [rider, m] of riderMap) { let counts = slots.map((_, i) => m.get(i) || 0);
                    riderRows.push({ rider, counts, total: counts.reduce((a, b) => a + b, 0) }); }
                riderRows.sort((a, b) => b.total - a.total);
                let totalOrders = slotOrders.reduce((a, b) => a + b, 0),
                    totalRiders = new Set(valid.map(v => v.rider)).size;
                let summary = [{ type: '时段单量', values: slotOrders, total: totalOrders }, { type: '时段人数',
                    values: slotRiders, total: totalRiders }, { type: '时段效率', values: eff.map(v => Math.round(v * 10) /
                        10), total: totalRiders ? (totalOrders / totalRiders).toFixed(1) : '0' }];
                return { timeSlotsRaw: slots, summaryRows: summary, riderDisplay: riderRows.map(r => ({ rider: r.rider,
                        values: r.counts, total: r.total })), efficiencyRaw: eff, rawOrders: slotOrders,
                    rawRiders: slotRiders, rawEffValues: eff };
            }

            function computeBlockStats() {
                if (!workbookData || !currentMapping.orderBlock || !currentMapping.orderRider) throw new Error('缺少区块映射');
                const data = workbookData.data,
                    blockCol = currentMapping.orderBlock,
                    riderCol = currentMapping.orderRider,
                    sCol = currentMapping.orderStatus;
                const blockCounts = new Map(),
                    riderBlockMap = new Map();
                let totalOrders = 0,
                    validRiderBlockCount = 0;
                for (let row of data) { if (!isDeliveredOrder(row, sCol)) continue; let rider = String(row[riderCol] || '')
                        .trim(); let block = String(row[blockCol] || '').trim(); if (!block) continue;
                    totalOrders++;
                    blockCounts.set(block, (blockCounts.get(block) || 0) + 1); if (rider) { validRiderBlockCount++; if (!
                            riderBlockMap.has(rider)) riderBlockMap.set(rider, new Map()); const riderMap = riderBlockMap.get(
                            rider);
                        riderMap.set(block, (riderMap.get(block) || 0) + 1); } }
                if (totalOrders === 0) throw new Error('无有效订单（请检查订单状态是否为"妥投"');
                const sortedBlocks = Array.from(blockCounts.keys()).sort((a, b) => getBlockSortKey(a) - getBlockSortKey(
                b));
                const blockOrders = sortedBlocks.map(b => blockCounts.get(b) || 0);
                const riderRows = [];
                for (let [rider, blockMap] of riderBlockMap) { const counts = sortedBlocks.map(b => blockMap.get(b) || 0); const
                        total = counts.reduce((s, v) => s + v, 0);
                    riderRows.push({ rider, counts, total }); }
                riderRows.sort((a, b) => b.total - a.total);
                return { blocks: sortedBlocks, blockOrders, totalOrders, riderRows, validRiderBlockCount };
            }

            function renderBlockTable(stats) {
                const { blocks, blockOrders, totalOrders, riderRows, validRiderBlockCount } = stats;
                if (!blocks.length) { resultTableHead.innerHTML = '<tr><th>提示</th></tr>';
                    resultTableBody.innerHTML = '<tr><td>暂无区块数据</td></tr>'; return; }
                let thead =
                    `<tr><th>区块</th><th>总计</th>${blocks.map(b=>`<th>${b}</th>`).join('')}</tr>`;
                resultTableHead.innerHTML = thead;
                const percentages = blockOrders.map(v => totalOrders ? ((v / totalOrders) * 100).toFixed(2) + '%' :
                    '0.00%');
                const validPercent = totalOrders ? ((validRiderBlockCount / totalOrders) * 100).toFixed(2) + '%' : '0.00%';
                let body =
                    `<tr class="summary-row"><td style="background:#fde68a;">单量</td><td>${totalOrders}</td>${blockOrders.map(v=>`<td style="font-weight:700;">${v}</td>`).join('')}</tr>`;
                body +=
                    `<tr class="summary-row"><td style="background:#fef9e3;">占比</td><td>${validPercent}</td>${percentages.map(p=>`<td>${p}</td>`).join('')}</tr>`;
                let sep = `<td style="background:#cbd5e6;">────────</td><td style="background:#cbd5e6;">─</td>` + blocks.map(
                    () => '<td style="background:#cbd5e6;">─</td>').join('');
                body += `<tr class="separator-row">${sep}</tr>`;
                let headerRow =
                    `<td style="background:#f1f5f9;font-weight:700;">姓名</td><td style="background:#f1f5f9;font-weight:700;">单量</td>`;
                blocks.forEach(b => headerRow +=
                    `<td style="background:#f1f5f9;font-weight:700;">${b}</td>`);
                body += `<tr class="block-header-row">${headerRow}</tr>`;
                riderRows.forEach(r => { const indexed = r.counts.map((v, i) => ({ val: v, idx: i }));
                    indexed.sort((a, b) => b.val - a.val); const rankMap = new Map(); let rank = 1; for (let item of indexed) { if (
                            item.val <= 0) break; if (rank === 1) rankMap.set(item.idx, 'red'); else if (rank === 2) rankMap
                        .set(item.idx, 'yellow'); else if (rank === 3) rankMap.set(item.idx, 'green'); else rankMap.set(item
                            .idx, 'gray');
                        rank++; } let cells = `<td>${r.rider}</td><td>${r.total}</td>`;
                    r.counts.forEach((cnt, i) => { if (cnt === 0) cells += '<td></td>'; else { const rank = rankMap.get(
                            i); let cls = rank === 'red' ? 'red-circle-bg' : (rank === 'yellow' ?
                            'yellow-circle-bg' : (rank === 'green' ? 'green-circle-bg' :
                                'gray-circle-bg'));
                        cells +=
                        `<td><span class="cell-number-circle ${cls}">${cnt}</span></td>`; } });
                    body += `<tr>${cells}</tr>`; });
                resultTableBody.innerHTML = body;
                updateStatus('区块占比视图', `${blocks.length}个区块 · ${totalOrders}单`, 'success');
            }

            function renderTableWithHeatmap(struct, shifts) {
                const { timeSlotsRaw, summaryRows, riderDisplay, efficiencyRaw, rawOrders, rawRiders, rawEffValues } = struct;
                const hasAttendance = shifts && shifts.size > 0;
                let h = '<tr><th>指标/骑手</th>';
                timeSlotsRaw.forEach(s => h +=
                    `<th><span class="slot-start">${s.startHour.toString().padStart(2,'0')}:${s.startMin.toString().padStart(2,'0')}</span><span class="slot-end">↓${s.endHour.toString().padStart(2,'0')}:${s.endMin.toString().padStart(2,'0')}</span></th>`
                    );
                h += '<th>总计</th></tr>';
                resultTableHead.innerHTML = h;
                const range = (arr, dMin, dMax) => { if (!arr?.length) return { min: dMin, max: dMax }; let min = Math.min(
                        ...arr, dMin),
                        max = Math.max(...arr, dMax); return { min, max: max === min ? dMax : max }; };
                const oR = range(rawOrders, 0, 1),
                    rR = range(rawRiders, 0, 1),
                    eR = range(rawEffValues, 0, 0.1);
                let body = '';
                summaryRows.forEach((s, idx) => { let cells =
                        `<td style="background:#d0f0c0;font-weight:700;">${s.type}</td>`;
                    s.values.forEach((v, i) => { let bg; if (idx === 0) bg = getHeatColor(v, oR.min, oR.max); else if (idx ===
                            1) bg = getHeatColor(v, rR.min, rR.max); else bg = getHeatColor(parseFloat(v), eR.min, eR
                        .max);
                        cells +=
                        `<td style="background:${bg};font-weight:700;">${v}</td>`; });
                    cells +=
                    `<td style="background:#d0f0c0;">${s.total}</td>`;
                    body += `<tr class="summary-row">${cells}</tr>`; });
                let sep = `<td style="background:#cbd5e6;">────────</td>` + Array(timeSlotsRaw.length).fill(
                    '<td style="background:#cbd5e6;">─</td>').join('') +
                    '<td style="background:#cbd5e6;">─</td>';
                body += `<tr class="separator-row">${sep}</tr>`;
                riderDisplay.forEach(r => { let shiftsArr = shifts.get(r.rider) || []; let isScheduled = hasAttendance &&
                        shiftsArr.length > 0; let cells =
                    `<td style="font-weight:700;">${r.rider}</td>`;
                    r.values.forEach((cnt, i) => { let avg = efficiencyRaw[i] || 0; let slot = timeSlotsRaw[i]; let
                            working = isScheduled ? isWorking(slot, shiftsArr) : !hasAttendance; let inner,
                            tdClass = ''; if (hasAttendance) { if (!working) { tdClass = 'non-working-bg';
                                inner = cnt > 0 ?
                                    `<div><span class="cell-number-circle white-circle-bg">${cnt}</span></div>` :
                                    '<div style="visibility:hidden;"> </div>'; } else if (cnt === 0) {
                                tdClass = 'zero-working-red';
                                inner = '<div style="visibility:hidden;"> </div>'; } else { tdClass =
                                    'working-bg';
                                inner =
                                    `<div><span class="cell-number-circle ${cnt>=avg?'green-circle-bg':'red-circle-bg'}">${cnt}</span></div>`; } } else {
                            inner =
                                `<div><span class="cell-number-circle ${cnt===0?'white-circle-bg':(cnt>=avg?'green-circle-bg':'red-circle-bg')}">${cnt}</span></div>`; }
                        cells +=
                        `<td class="${tdClass}">${inner}</td>`; });
                    cells +=
                    `<td style="font-weight:700;">${r.total}</td>`;
                    body += `<tr>${cells}</tr>`; });
                resultTableBody.innerHTML = body;
            }

            function extractStoreName() {
                if (!workbookData || !currentMapping.orderStore) return '';
                const col = currentMapping.orderStore;
                for (let row of workbookData.data)
                if (row[col]) return String(row[col]).trim().replace(/[\\/:*?"<>|]/g, '');
                return '';
            }

            async function generateReportHTML() {
                if (!structHalfHour || !structHour) { alert('请先生成统计表'); return ''; }
                const payload = { structHalfHour, structHour, blockStats: blockStats || null, typeStatsHalf: typeStatsHalf ||
                        null, typeStatsHour: typeStatsHour || null, blockTimeStatsHalf: blockTimeStatsHalf || null,
                    blockTimeStatsHour: blockTimeStatsHour || null, riderShifts: Array.from(riderShiftsMap.entries()),
                    riderTypeMap: Array.from(riderTypeMap.entries()), currentView: 'half', typeViewGran: typeViewGran,
                    currentFilterRider: '__ALL__' };
                const styles = document.querySelector('style').innerHTML;
                const heatLegendHtml = heatmapLegend.outerHTML.replace('<div class="legend"',
                    '<div class="legend" id="repHeatLegend"');
                const blockLegendHtml = blockLegend.outerHTML.replace('<div class="legend"',
                    '<div class="legend" id="repBlockLegend"');
                const typeLegendHtml = typeLegend.outerHTML.replace('<div class="legend"',
                    '<div class="legend" id="repTypeLegend"');
                const title = storeName ? `${storeName} · 骑手热力图` : '骑手热力图';
                const keyBytes = new Uint8Array(32);
                crypto.getRandomValues(keyBytes);
                const keyHex = Array.from(keyBytes).map(b => b.toString(16).padStart(2, '0')).join('');
                const keyPart1 = keyHex.substring(0, 32),
                    keyPart2 = keyHex.substring(32);
                const encoder = new TextEncoder();
                const dataBytes = encoder.encode(JSON.stringify(payload));
                const encrypted = new Uint8Array(dataBytes.length); for (let i = 0; i < dataBytes.length; i++) encrypted[i] =
                    dataBytes[i] ^ keyBytes[i % 32];
                const encBase64 = btoa(String.fromCharCode(...encrypted));
                const protectStyle =
                    `* { user-select: none !important; -webkit-user-select: none !important; } input, select, button { user-select: none; -webkit-user-select: none; }`;
                const reportScript = `
var _k1='${keyPart1}',_k2='${keyPart2}';
(function(){ var _key=_k1+_k2; var _enc='${encBase64}'; var _d=function(enc,keyHex){ var kb=new Uint8Array(keyHex.match(/.{1,2}/g).map(function(b){ return parseInt(b,16); })); var eb=Uint8Array.from(atob(enc),function(c){ return c.charCodeAt(0); }); var db=new Uint8Array(eb.length); for(var i=0;i<eb.length;i++) db[i]=eb[i]^kb[i%32]; return new TextDecoder().decode(db); }; var payload=JSON.parse(_d(_enc,_key)); startApp(payload); })();
function startApp(payload){
    var shiftsMap=new Map(payload.riderShifts), riderTypeMap=new Map(payload.riderTypeMap), view=payload.currentView, typeViewGran=payload.typeViewGran||'half', selectedRiders=new Set();
    var allRiders=payload.structHalfHour.riderDisplay.map(function(r){ return r.rider; });
    var thead=document.querySelector('#repTable thead'), tbody=document.querySelector('#repTable tbody'), searchInput=document.getElementById('repRiderSearchInput'), clearBtn=document.getElementById('repRiderClearBtn'), dropdown=document.getElementById('repRiderDropdown'), stats=document.getElementById('repStats'), viewGroup=document.getElementById('repViewGroup'), scrollWrap=document.getElementById('repScrollWrapper'), heatL=document.getElementById('repHeatLegend'), blockL=document.getElementById('repBlockLegend'), typeL=document.getElementById('repTypeLegend'), filterCompact=document.getElementById('repRiderFilterCompact'), typeGranToggle=document.getElementById('repTypeGranToggle'), typeGranText=document.getElementById('repTypeGranText');
    var isDragging=false,sx,sy,sl,st; scrollWrap.style.cursor='grab';
    function applyScrollLimits(){ var maxLeft=scrollWrap.scrollWidth-scrollWrap.clientWidth, maxTop=scrollWrap.scrollHeight-scrollWrap.clientHeight; scrollWrap.scrollLeft=Math.max(0,Math.min(scrollWrap.scrollLeft,maxLeft)); scrollWrap.scrollTop=Math.max(0,Math.min(scrollWrap.scrollTop,maxTop)); }
    function onDragStart(pageX,pageY){ isDragging=true; scrollWrap.style.cursor='grabbing'; sx=pageX-scrollWrap.offsetLeft; sy=pageY-scrollWrap.offsetTop; sl=scrollWrap.scrollLeft; st=scrollWrap.scrollTop; }
    function onDragMove(pageX,pageY){ if(!isDragging) return; var dx=pageX-scrollWrap.offsetLeft-sx, dy=pageY-scrollWrap.offsetTop-sy; var newLeft=sl-dx*1.5, newTop=st-dy*1.5; var maxLeft=scrollWrap.scrollWidth-scrollWrap.clientWidth, maxTop=scrollWrap.scrollHeight-scrollWrap.clientHeight; newLeft=Math.max(0,Math.min(newLeft,maxLeft)); newTop=Math.max(0,Math.min(newTop,maxTop)); scrollWrap.scrollLeft=newLeft; scrollWrap.scrollTop=newTop; }
    function onDragEnd(){ isDragging=false; scrollWrap.style.cursor='grab'; applyScrollLimits(); }
    scrollWrap.addEventListener('mousedown',function(e){ if(e.target.closest('button,select,.view-option,input')) return; e.preventDefault(); onDragStart(e.pageX,e.pageY); });
    window.addEventListener('mousemove',function(e){ if(!isDragging) return; e.preventDefault(); onDragMove(e.pageX,e.pageY); });
    window.addEventListener('mouseup',onDragEnd);
    scrollWrap.addEventListener('touchstart',function(e){ if(e.target.closest('button,select,.view-option,input')) return; if(e.touches.length!==1) return; e.preventDefault(); onDragStart(e.touches[0].pageX,e.touches[0].pageY); },{passive:false});
    scrollWrap.addEventListener('touchmove',function(e){ if(!isDragging) return; e.preventDefault(); onDragMove(e.touches[0].pageX,e.touches[0].pageY); },{passive:false});
    scrollWrap.addEventListener('touchend',onDragEnd); scrollWrap.addEventListener('touchcancel',onDragEnd);
    window.addEventListener('mouseleave',function(){ if(isDragging) onDragEnd(); }); document.addEventListener('touchcancel',function(){ if(isDragging) onDragEnd(); });
    scrollWrap.addEventListener('scroll',function(){ if(!isDragging) applyScrollLimits(); });
    function renderDropdown(filterText){ var f=filterText||''; var filtered=f?allRiders.filter(function(r){ return r.toLowerCase().indexOf(f.toLowerCase())!==-1; }):allRiders; if(filtered.length===0){ dropdown.innerHTML='<div class="rider-no-result">😕 无匹配骑手</div>'; return; } dropdown.innerHTML=filtered.map(function(r){ var checked=selectedRiders.has(r); return '<div class="rider-option'+(checked?' checked':'')+'" data-value="'+r+'"><span class="rider-checkbox">✓</span>'+r+'</div>'; }).join(''); }
    function openDropdown(){ dropdown.classList.add('show'); renderDropdown(searchInput.value); }
    function closeDropdown(){ dropdown.classList.remove('show'); }
    searchInput.addEventListener('focus',openDropdown); searchInput.addEventListener('input',openDropdown);
    searchInput.addEventListener('keydown',function(e){ if(e.key==='Escape'){ closeDropdown(); searchInput.blur(); } });
    dropdown.addEventListener('click',function(e){ e.stopPropagation(); var opt=e.target.closest('.rider-option'); if(!opt) return; var val=opt.dataset.value; selectedRiders.has(val)?selectedRiders.delete(val):selectedRiders.add(val); renderDropdown(searchInput.value); searchInput.focus(); updateUI(); });
    // 【修改4】清空按钮点击后不触发下拉
clearBtn.addEventListener('click',function(e){
    e.stopPropagation();
    selectedRiders.clear();
    searchInput.value='';
    renderDropdown();
    updateUI();
    // 移除 focus，避免移动端弹出键盘
    dropdown.classList.remove('show');
});    document.addEventListener('click',function(e){ if(!filterCompact.contains(e.target)) closeDropdown(); });
    function getHeatColor(v,min,max){if(max===min||max<=0)return '#b9f6ca';var t=(v-min)/(max-min);var r=Math.floor(34+205*t),g=Math.floor(197-129*t),b=Math.floor(94-26*t);return 'rgb('+r+','+g+','+b+')';}
    function isWorking(slot,shifts){if(!shifts||!shifts.length)return true;var ss=slot.startHour*60+slot.startMin,se=slot.endHour*60+slot.endMin;return shifts.some(function(s){ return (s.startHour*60+s.startMin)<se && (s.endHour*60+s.endMin)>ss; });}
    function renderHeat(struct){ var slots=struct.timeSlotsRaw, eff=struct.efficiencyRaw; var range=function(a,dMin,dMax){if(!a||!a.length)return{min:dMin,max:dMax};var min=Math.min.apply(null,a.concat(dMin)),max=Math.max.apply(null,a.concat(dMax));return{min:min,max:max===min?dMax:max};}; var oR=range(struct.rawOrders,0,1),rR=range(struct.rawRiders,0,1),eR=range(struct.rawEffValues,0,0.1); var display=selectedRiders.size>0?struct.riderDisplay.filter(function(r){ return selectedRiders.has(r.rider); }):struct.riderDisplay; thead.innerHTML='<tr><th>指标/骑手</th>'+slots.map(function(s){ return '<th><span class="slot-start">'+s.startHour.toString().padStart(2,'0')+':'+s.startMin.toString().padStart(2,'0')+'</span><span class="slot-end">↓'+s.endHour.toString().padStart(2,'0')+':'+s.endMin.toString().padStart(2,'0')+'</span></th>'; }).join('')+'<th>总计</th></tr>'; var body=''; struct.summaryRows.forEach(function(s,idx){ body+='<tr class="summary-row"><td style="background:#d0f0c0;">'+s.type+'</td>'; s.values.forEach(function(v,i){ var bg=idx===0?getHeatColor(v,oR.min,oR.max):(idx===1?getHeatColor(v,rR.min,rR.max):getHeatColor(parseFloat(v),eR.min,eR.max)); body+='<td style="background:'+bg+';">'+v+'</td>'; }); body+='<td style="background:#d0f0c0;">'+s.total+'</td></tr>'; }); body+='<tr class="separator-row"><td style="background:#cbd5e6;">────────</td>'+slots.map(function(){ return '<td style="background:#cbd5e6;">─</td>'; }).join('')+'<td style="background:#cbd5e6;">─</td></tr>'; display.forEach(function(r){ var shifts=shiftsMap.get(r.rider)||[]; var isScheduled=shiftsMap.size>0&&shifts.length>0; body+='<tr><td>'+r.rider+'</td>'; r.values.forEach(function(cnt,i){ var avg=eff[i]||0; var slot=slots[i]; var working=isScheduled?isWorking(slot,shifts):!(shiftsMap.size>0); var inner='',cls=''; if(shiftsMap.size>0){ if(!working){ cls='non-working-bg'; inner=cnt>0?'<div><span class="cell-number-circle white-circle-bg">'+cnt+'</span></div>':'<div style="visibility:hidden;"> </div>'; } else if(cnt===0){ cls='zero-working-red'; inner='<div style="visibility:hidden;"> </div>'; } else { cls='working-bg'; inner='<div><span class="cell-number-circle '+(cnt>=avg?'green-circle-bg':'red-circle-bg')+'">'+cnt+'</span></div>'; } } else { inner='<div><span class="cell-number-circle '+(cnt===0?'white-circle-bg':(cnt>=avg?'green-circle-bg':'red-circle-bg'))+'">'+cnt+'</span></div>'; } body+='<td class="'+cls+'">'+inner+'</td>'; }); body+='<td>'+r.total+'</td></tr>'; }); tbody.innerHTML=body; }
    function renderBlock(stats){ if(!stats){ tbody.innerHTML='<tr><td>暂无区块数据</td></tr>'; stats.textContent='区块视图 · 无数据'; return; } var blocks=stats.blocks,blockOrders=stats.blockOrders,totalOrders=stats.totalOrders,riderRows=stats.riderRows,validRiderBlockCount=stats.validRiderBlockCount; var display=selectedRiders.size>0?riderRows.filter(function(r){ return selectedRiders.has(r.rider); }):riderRows; thead.innerHTML='<tr><th>区块</th><th>总计</th>'+blocks.map(function(b){ return '<th>'+b+'</th>'; }).join('')+'</tr>'; var body='<tr class="summary-row"><td style="background:#fde68a;">单量</td><td>'+totalOrders+'</td>'+blockOrders.map(function(v){ return '<td>'+v+'</td>'; }).join('')+'</tr>'; body+='<tr class="summary-row"><td style="background:#fef9e3;">占比</td><td>'+(totalOrders?((validRiderBlockCount/totalOrders)*100).toFixed(2)+'%':'0.00%')+'</td>'+blockOrders.map(function(v){ return '<td>'+(totalOrders?((v/totalOrders)*100).toFixed(2)+'%':'0.00%')+'</td>'; }).join('')+'</tr>'; body+='<tr class="separator-row"><td style="background:#cbd5e6;">────────</td><td style="background:#cbd5e6;">─</td>'+blocks.map(function(){ return '<td style="background:#cbd5e6;">─</td>'; }).join('')+'</tr>'; var headerRow='<td style="background:#f1f5f9;font-weight:700;">姓名</td><td style="background:#f1f5f9;font-weight:700;">单量</td>'; blocks.forEach(function(b){ headerRow+='<td style="background:#f1f5f9;font-weight:700;">'+b+'</td>'; }); body+='<tr class="block-header-row">'+headerRow+'</tr>'; display.forEach(function(r){ var indexed=r.counts.map(function(v,i){ return {val:v,idx:i}; }); indexed.sort(function(a,b){ return b.val-a.val; }); var rankMap=new Map(); var rank=1; indexed.forEach(function(it){ if(it.val<=0) return; if(rank===1) rankMap.set(it.idx,'red'); else if(rank===2) rankMap.set(it.idx,'yellow'); else if(rank===3) rankMap.set(it.idx,'green'); else rankMap.set(it.idx,'gray'); rank++; }); body+='<tr><td>'+r.rider+'</td><td>'+r.total+'</td>'; r.counts.forEach(function(cnt,i){ if(cnt===0) body+='<td></td>'; else { var cls='white-circle-bg'; var rk=rankMap.get(i); if(rk==='red') cls='red-circle-bg'; else if(rk==='yellow') cls='yellow-circle-bg'; else if(rk==='green') cls='green-circle-bg'; else if(rk==='gray') cls='gray-circle-bg'; body+='<td><span class="cell-number-circle '+cls+'">'+cnt+'</span></td>'; } }); body+='</tr>'; }); tbody.innerHTML=body; }
    // 【修改1+2】类型视图渲染 - 每行独立热力，区块按总单量降序
    function renderTypeTable(typeStats,blockTimeStats){ if(!typeStats||!typeStats.typeRows.length){ thead.innerHTML='<tr><th>提示</th></tr>'; tbody.innerHTML='<tr><td>无骑手类型数据，请确保考勤表包含骑手类型列并在映射中设置</td></tr>'; return; } var slots=typeStats.slots; var typeRows=typeStats.typeRows; var h='<tr><th>骑手类型 / 区块</th>'; slots.forEach(function(s){ h+='<th><span class="slot-start">'+s.startHour.toString().padStart(2,'0')+':'+s.startMin.toString().padStart(2,'0')+'</span><span class="slot-end">↓'+s.endHour.toString().padStart(2,'0')+':'+s.endMin.toString().padStart(2,'0')+'</span></th>'; }); h+='<th>总单量</th><th>总人数</th></tr>'; thead.innerHTML=h; var body='';
    typeRows.forEach(function(r){ body+='<tr><td style="font-weight:700;background:#f0fdf4;">'+r.type+'</td>'; var rowOrders=r.orders; var rowMin=Math.min.apply(null,[0].concat(rowOrders)); var rowMax=Math.max.apply(null,[1].concat(rowOrders)); r.orders.forEach(function(v){ var bg=getHeatColor(v,rowMin,rowMax); body+='<td style="background:'+bg+';font-weight:600;">'+v+'</td>'; }); body+='<td style="font-weight:700;background:#f0fdf4;">'+r.totalOrders+'</td><td style="background:#f0fdf4;">'+r.totalRiders+'</td></tr>'; });
    if(blockTimeStats&&blockTimeStats.blockRows.length>0){ var blockRows=blockTimeStats.blockRows; var sortedBlockRows=blockRows.slice().sort(function(a,b){ return b.total-a.total; }); var sep='<td style="background:#cbd5e6;">────────</td>'+slots.map(function(){ return '<td style="background:#cbd5e6;">─</td>'; }).join('')+'<td style="background:#cbd5e6;">─</td><td style="background:#cbd5e6;">─</td>'; body+='<tr class="separator-row">'+sep+'</tr>'; sortedBlockRows.forEach(function(r){ body+='<tr><td style="font-weight:700;background:#eef2ff;">📦 '+r.block+'</td>'; var brOrders=r.orders; var brMin=Math.min.apply(null,[0].concat(brOrders)); var brMax=Math.max.apply(null,[1].concat(brOrders)); r.orders.forEach(function(v){ var bg=getHeatColor(v,brMin,brMax); body+='<td style="background:'+bg+';font-weight:600;">'+v+'</td>'; }); body+='<td style="font-weight:700;background:#eef2ff;">'+r.total+'</td><td style="background:#eef2ff;">—</td></tr>'; }); } tbody.innerHTML=body; }
    function switchView(v){
        if(v==='type'){ if(view==='half'||view==='hour') typeViewGran=view; }
        if(v!==view){ scrollWrap.scrollLeft=0; scrollWrap.scrollTop=0; }
        view=v;
        document.querySelectorAll('.view-option').forEach(function(o){ o.classList.remove('active'); });
        var activeOption=document.querySelector('.view-option[data-view="'+view+'"]');
        if(activeOption) activeOption.classList.add('active');
        heatL.style.display=(view==='half'||view==='hour')?'flex':'none';
        blockL.style.display=(view==='block')?'flex':'none';
        typeL.style.display=(view==='type')?'flex':'none';
        document.body.classList.remove('block-view-active','type-view-active');
        if(view==='block') document.body.classList.add('block-view-active');
        if(view==='type') document.body.classList.add('type-view-active');
        if(view==='type'){ filterCompact.style.display='none'; typeGranToggle.style.display='inline-flex'; if(typeGranText) typeGranText.value=typeViewGran==='half'?'点击切换小时':'点击切换半小时'; }
        else { typeGranToggle.style.display='none'; filterCompact.style.display='inline-flex'; }
        updateUI();
    }
    typeGranToggle.addEventListener('click',function(){ if(view!=='type') return; typeViewGran=typeViewGran==='half'?'hour':'half'; if(typeGranText) typeGranText.value=typeViewGran==='half'?'点击切换小时':'点击切换半小时'; updateUI(); });
    function updateUI(){
        if(view==='block'){ if(payload.blockStats) renderBlock(payload.blockStats); else { tbody.innerHTML='<tr><td>请在主应用中配置区块列并重新导出</td></tr>'; stats.textContent='区块视图 · 无数据'; } if(payload.blockStats) stats.textContent='区块视图 · '+(selectedRiders.size>0?selectedRiders.size:payload.blockStats.riderRows.length)+'位骑手 · '+payload.blockStats.totalOrders+'单'; }
        else if(view==='type'){ var ts=typeViewGran==='half'?payload.typeStatsHalf:payload.typeStatsHour; var bts=typeViewGran==='half'?payload.blockTimeStatsHalf:payload.blockTimeStatsHour; renderTypeTable(ts,bts); if(ts) stats.textContent='骑手类型 · '+ts.typeRows.length+'种类型'; else stats.textContent='骑手类型 · 无数据'; }
        else { var struct=view==='half'?payload.structHalfHour:payload.structHour; renderHeat(struct); var cnt=selectedRiders.size>0?selectedRiders.size:struct.riderDisplay.length; var viewName=view==='half'?'半小时':(view==='hour'?'小时':''); stats.textContent=viewName+'视图 · '+cnt+'位骑手 · '+struct.rawOrders.reduce(function(a,b){ return a+b; },0)+'单'; }
    }
    viewGroup.addEventListener('click',function(e){ var opt=e.target.closest('.view-option'); if(!opt) return; switchView(opt.dataset.view); });
    switchView(payload.currentView);
}
setInterval(function(){ var start=performance.now(); debugger; var end=performance.now(); if(end-start>100){ document.body.innerHTML='<h2 style="text-align:center;margin-top:100px;">检测到调试行为，报告已锁定</h2>'; throw new Error('Debugger detected'); } },1000);
`;
                return `<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>${title}</title><style>${styles} ${protectStyle} @media (max-width: 768px) { .report-control-row { flex-direction: column !important; align-items: center !important; } .rider-filter-compact { margin: 0 auto !important; } } .table-scroll-wrapper { overscroll-behavior: contain !important; touch-action: pan-x pan-y !important; } .type-view-active .frozen-table tbody tr td, .type-view-active .frozen-table tbody tr th { position: static !important; z-index: auto !important; } .type-view-active .frozen-table tbody tr td:first-child, .type-view-active .frozen-table tbody tr th:first-child { position: sticky !important; left: 0; z-index: 100 !important; box-shadow: 2px 0 5px -2px rgba(0,0,0,0.15); border-right: 3px solid #1a1a1a !important; background-color: #fef9e3 !important; } .type-view-active .frozen-table tbody tr td:first-child { font-weight: 600; text-align: right; }</style></head>
<body style="background:white; padding:16px;" onselectstart="return false;" oncontextmenu="return false;">
<div style="max-width:1600px; margin:0 auto;">
<h1 style="background:linear-gradient(135deg,#1e6f3f,#2c8c4a);-webkit-background-clip:text;background-clip:text;color:transparent;text-align:center;">📊 ${title}</h1>
<div class="sub" style="text-align:center;">生成时间: ${new Date().toLocaleString()}</div>
<div class="report-control-row" style="display:flex; gap:16px; justify-content:center; margin-bottom:16px; flex-wrap:wrap; align-items:center;">
    <div class="view-toggle-group" id="repViewGroup">
        <div class="view-option active" data-view="half">⏱️ 半小时</div>
        <div class="view-option" data-view="hour">⏰ 小时</div>
        <div class="view-option" data-view="block">🧩 区块</div>
        <div class="view-option" data-view="type">👥 类型</div>
    </div>
    <div class="rider-filter-compact" id="repRiderFilterCompact">
        <span class="rider-filter-label">🔍 骑手</span>
        <input type="text" class="rider-search-input" id="repRiderSearchInput" placeholder="搜索或点击..." autocomplete="off">
        <button class="rider-clear-btn" id="repRiderClearBtn">✖️ 清空</button>
        <div class="rider-dropdown" id="repRiderDropdown"></div>
    </div>
    <div class="rider-filter-compact" id="repTypeGranToggle" style="display:none; cursor:pointer;">
        <span class="rider-filter-label">🔀 粒度</span>
        <input type="text" class="rider-search-input" id="repTypeGranText" value="点击切换小时" readonly style="width:130px; text-align:center; cursor:pointer; font-weight:500; color:#1e6f3f;">
    </div>
    <span id="repStats" style="font-size:0.8rem;"></span>
</div>
<div class="table-fixed-container"><div class="table-scroll-wrapper" id="repScrollWrapper"><table class="frozen-table" id="repTable"><thead></thead><tbody></tbody></table></div></div>
${heatLegendHtml}
${blockLegendHtml}
${typeLegendHtml}
</div>
<script>${reportScript}<\/script></body></html>`;
            }

            async function exportHTMLReport() {
                if (!structHalfHour && !structHour) { updateStatus('请先生成统计表', '', 'error'); return; }
                try { const html = await generateReportHTML(); if (!html) return; const blob = new Blob([html], { type: 'text/html' });
                    const a = document.createElement('a');
                    a.download = `${storeName||'骑手热力'}_${new Date().toISOString().slice(0,10)}.html`;
                    a.href = URL.createObjectURL(blob);
                    a.click();
                    URL.revokeObjectURL(a.href);
                    updateStatus('报告已导出 (加密防护)', 'success'); } catch (e) { updateStatus('导出失败', '', 'error'); }
            }

            function renderPreview(data, cols) {
                if (!data?.length) return;
                let h = '<thead><tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
                data.slice(0, 80).forEach(r => h += '<tr>' + cols.map(c => `<td>${String(r[c]||'').substring(0,30)}</td>`)
                    .join('') + '</tr>');
                previewTable.innerHTML = h + '</tbody>';
                previewArea.style.display = 'block';
            }
            async function autoAnalyzeIfReady() {
                if (!workbookData?.data?.length || !currentMapping.orderTime || !currentMapping.orderRider) return;
                try { structHalfHour = analyzeData('半小时');
                    structHour = analyzeData('小时'); if (currentMapping.orderBlock) blockStats = computeBlockStats();
                    typeStatsHalf = computeTypeStats('半小时', null);
                    typeStatsHour = computeTypeStats('小时', null);
                    blockTimeStatsHalf = computeBlockTimeStats('半小时', null);
                    blockTimeStatsHour = computeBlockTimeStats('小时', null);
                    updateRiderFilterUI(structHalfHour.riderDisplay.map(r => r.rider));
                    exportReportBtn.disabled = false;
                    renderCurrentView(); } catch (e) { updateStatus(`自动分析失败: ${e.message}`, '', 'warning'); }
            }

            function openMappingModal() {
                populateSelect(mapOrderRider, workbookData?.columns || [], currentMapping.orderRider);
                populateSelect(mapOrderTime, workbookData?.columns || [], currentMapping.orderTime);
                populateSelect(mapOrderStore, workbookData?.columns || [], currentMapping.orderStore);
                populateSelect(mapOrderBlock, workbookData?.columns || [], currentMapping.orderBlock);
                populateSelect(mapOrderStatus, workbookData?.columns || [], currentMapping.orderStatus);
                populateSelect(mapAttRider, attendanceWorkbook?.columns || [], currentMapping.attRider);
                populateSelect(mapAttStart, attendanceWorkbook?.columns || [], currentMapping.attStart);
                populateSelect(mapAttEnd, attendanceWorkbook?.columns || [], currentMapping.attEnd);
                populateSelect(mapAttStatus, attendanceWorkbook?.columns || [], currentMapping.attStatus);
                populateSelect(mapAttRiderType, attendanceWorkbook?.columns || [], currentMapping.attRiderType);
                mappingModal.style.display = 'flex';
            }

            fileInput.onchange = async e => { const f = e.target.files[0]; if (!f) return;
                orderFileTrigger.textContent = `📄 ${f.name}`;
                updateStatus('加载订单...', f.name, 'info'); try { const { columns, data } = await loadExcel(f);
                    workbookData = { columns, data };
                    renderPreview(data, columns); ['orderRider', 'orderTime', 'orderStore', 'orderBlock', 'orderStatus']
                        .forEach(k => { if (!columns.includes(currentMapping[k])) { let m = columns.find(c => new RegExp(
                                k === 'orderRider' ? '骑手|配送员' : (k === 'orderTime' ? '时间|完成' : (k ===
                                    'orderBlock' ? '区块|区域' : (k === 'orderStatus' ? '状态' :
                                        '门店|店铺')))).test(c)); if (m) currentMapping[k] = m; } });
                    storeName = extractStoreName();
                    updateStatus('订单加载成功', `${data.length}行`, 'success');
                    await autoAnalyzeIfReady(); } catch (err) { orderFileTrigger.textContent =
                    '📁 点击选择订单文件';
                    updateStatus(`读取失败: ${err.message}`, '', 'error'); }
                fileInput.value = ''; };
            attendanceInput.onchange = async e => { const f = e.target.files[0]; if (!f) { riderShiftsMap.clear();
                    riderTypeMap.clear();
                    attFileTrigger.textContent = '📁 点击选择考勤文件(可选)';
                    attendanceWorkbook = null;
                    await autoAnalyzeIfReady(); return; }
                attFileTrigger.textContent = `📄 ${f.name}`; try { const wb = await loadExcel(f);
                    attendanceWorkbook = wb; ['attRider', 'attStart', 'attEnd', 'attRiderType'].forEach(k => { if (!wb
                            .columns.includes(currentMapping[k])) { let m = wb.columns.find(c => new RegExp(k ===
                                'attRider' ? '骑手' : (k === 'attStart' ? '开始' : (k === 'attEnd' ? '结束' :
                                    k === 'attRiderType' ? '类型' : ''))).test(c)); if (m) currentMapping[k] = m; } });
                    riderShiftsMap = parseAttendance(currentMapping); let cnt = 0; for (let v of riderShiftsMap.values())
                        cnt += v.length;
                    await autoAnalyzeIfReady();
                    updateStatus(cnt ? '考勤加载成功' : '未找到有效班次', cnt ?
                        `${riderShiftsMap.size}人·${cnt}班次` : '全时段工作', cnt ? 'success' : 'warning'); } catch (
                    err) { riderShiftsMap.clear();
                    riderTypeMap.clear();
                    attFileTrigger.textContent = '📁 点击选择考勤文件(可选)';
                    updateStatus(`读取失败: ${err.message}`, '', 'error'); }
                attendanceInput.value = ''; };
            analyzeBtn.onclick = performAnalysis;
            exportReportBtn.onclick = exportHTMLReport;
            togglePreviewBtn.onclick = () => { previewVisible = !previewVisible;
                previewContainer.style.display = previewVisible ? 'block' : 'none';
                togglePreviewBtn.innerText = previewVisible ? '折叠' : '展开'; };
            mappingConfigBtn.onclick = openMappingModal;
            closeModalBtn.onclick = () => mappingModal.style.display = 'none';
            applyMappingBtn.onclick = applyMappingAndAnalyze;
            window.onclick = e => { if (e.target === mappingModal) mappingModal.style.display = 'none'; };

            previewContainer.style.display = "block";
            progressBar.style.display = "none";
            setActiveView('half');
        })();