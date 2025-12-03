// ==================== CONFIG ====================
const API_BASE = 'http://localhost:5000/api';

// ==================== STATE ====================
let currentGymId = null;
let currentGymName = null;
let currentAdminUsername = null;
let allMembers = [];
let allTrainers = [];
let allPrograms = [];
let allExercises = [];

// ==================== LOGIN ====================
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentGymId = data.gym_id;
            currentAdminUsername = username;
            localStorage.setItem('gymId', currentGymId);
            localStorage.setItem('adminUsername', username);
            showDashboard();
        } else {
            showLoginAlert(data.error || 'Giriş başarısız', 'danger');
        }
    } catch (error) {
        showLoginAlert('Sunucuya bağlanılamadı', 'danger');
    }
});

function showLoginAlert(message, type) {
    document.getElementById('loginAlert').innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// ==================== DASHBOARD ====================
async function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('dashboardPage').classList.remove('d-none');
    
    await loadGymInfo();
    await loadDashboardData();
}

async function loadGymInfo() {
    try {
        const response = await fetch(`${API_BASE}/gyms/${currentGymId}`);
        if (response.ok) {
            const gym = await response.json();
            currentGymName = gym.name;
            document.getElementById('gymName').innerHTML = `<i class="bi bi-building me-2"></i>${gym.name}`;
            
            // Settings
            document.getElementById('settingsGymName').value = gym.name;
            document.getElementById('settingsGymLocation').value = gym.location || '';
            document.getElementById('settingsGymCapacity').value = gym.capacity || 0;
            document.getElementById('settingsAdminUsername').value = currentAdminUsername;
            document.getElementById('settingsGymId').value = currentGymId;
        }
    } catch (error) {
        document.getElementById('gymName').innerHTML = `<i class="bi bi-building me-2"></i>Salon #${currentGymId}`;
    }
}

async function loadDashboardData() {
    await Promise.all([loadStats(), loadMembers(), loadTrainers(), loadPrograms(), loadExercises()]);
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/gym/${currentGymId}/stats`);
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('statTotalMembers').textContent = stats.total_members || 0;
            document.getElementById('statActiveMembers').textContent = stats.active_members || 0;
            document.getElementById('statPeopleInside').textContent = stats.people_inside || 0;
            document.getElementById('statTotalTrainers').textContent = allTrainers.length || 0;
        }
    } catch (error) {
        console.log('Stats error:', error);
    }
}

// ==================== MEMBERS ====================
async function loadMembers() {
    try {
        const response = await fetch(`${API_BASE}/admin/gym/${currentGymId}/members`);
        if (response.ok) {
            allMembers = await response.json();
            renderMembersTable(allMembers);
            renderRecentMembers(allMembers.slice(0, 5));
        }
    } catch (error) {
        console.log('Members error:', error);
    }
}

function renderMembersTable(members) {
    const tbody = document.getElementById('allMembersTable');
    if (members.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4">Henüz üye yok</td></tr>';
        return;
    }
    
    tbody.innerHTML = members.map(m => `
        <tr>
            <td>#${m.member_id}</td>
            <td>${m.name}</td>
            <td>${m.email}</td>
            <td><span class="badge ${m.type === 'timed' ? 'badge-timed' : 'badge-credit'}">${m.type === 'timed' ? 'Süreli' : 'Kredili'}</span></td>
            <td>${m.type === 'timed' ? (m.remaining_days !== null ? m.remaining_days + ' gün' : '-') : ((m.credit_total - m.credit_used) + ' giriş')}</td>
            <td><span class="badge ${m.is_active ? 'badge-active' : 'badge-inactive'}">${m.is_active ? 'Aktif' : 'Pasif'}</span></td>
            <td>
                <button class="btn btn-success action-btn" onclick="openAddCreditModal(${m.membership_id}, '${m.name}', '${m.type}')" title="Bakiye Ekle">
                    <i class="bi bi-plus"></i>
                </button>
                <button class="btn btn-warning action-btn" onclick="openEditMemberModal(${m.membership_id}, '${m.name}', '${m.type}', ${m.remaining_days || 30}, ${m.credit_total || 0}, ${m.credit_used || 0}, ${m.is_active ? 1 : 0})" title="Düzenle">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-danger action-btn" onclick="openDeleteModal(${m.membership_id}, 'member', '${m.name}')" title="Sil">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderRecentMembers(members) {
    const tbody = document.getElementById('recentMembersTable');
    if (members.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4">Henüz üye yok</td></tr>';
        return;
    }
    
    tbody.innerHTML = members.map(m => `
        <tr>
            <td>${m.name}</td>
            <td>${m.email}</td>
            <td><span class="badge ${m.type === 'timed' ? 'badge-timed' : 'badge-credit'}">${m.type === 'timed' ? 'Süreli' : 'Kredili'}</span></td>
            <td><span class="badge ${m.is_active ? 'badge-active' : 'badge-inactive'}">${m.is_active ? 'Aktif' : 'Pasif'}</span></td>
        </tr>
    `).join('');
}

// Member Search
document.getElementById('memberSearch').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allMembers.filter(m => 
        m.name.toLowerCase().includes(query) || 
        m.email.toLowerCase().includes(query)
    );
    renderMembersTable(filtered);
});

// Add Member
document.getElementById('membershipType').addEventListener('change', (e) => {
    document.getElementById('timedOptions').classList.toggle('d-none', e.target.value !== 'timed');
    document.getElementById('creditOptions').classList.toggle('d-none', e.target.value !== 'credit');
});

document.getElementById('confirmAddMember').addEventListener('click', async () => {
    const email = document.getElementById('memberEmail').value;
    const type = document.getElementById('membershipType').value;
    const days = document.getElementById('membershipDays').value;
    const credits = document.getElementById('membershipCredits').value;
    
    if (!email) {
        showAlert('Email gerekli!', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/add-member`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gym_id: currentGymId,
                email,
                type,
                days: type === 'timed' ? parseInt(days) : null,
                credits: type === 'credit' ? parseInt(credits) : null
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addMemberModal')).hide();
            document.getElementById('memberEmail').value = '';
            showAlert('Üye başarıyla eklendi! 🎉', 'success');
            loadMembers();
            loadStats();
        } else {
            showAlert(data.error || 'Üye eklenemedi', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// Edit Member Modal
function openEditMemberModal(membershipId, name, type, remainingDays, creditTotal, creditUsed, isActive) {
    document.getElementById('editMembershipId').value = membershipId;
    document.getElementById('editMemberName').value = name;
    document.getElementById('editMembershipType').value = type;
    document.getElementById('editMemberDays').value = remainingDays || 30;
    document.getElementById('editCreditTotal').value = creditTotal || 0;
    document.getElementById('editMemberStatus').value = isActive;
    
    document.getElementById('editTimedOptions').classList.toggle('d-none', type !== 'timed');
    document.getElementById('editCreditOptions').classList.toggle('d-none', type !== 'credit');
    
    new bootstrap.Modal(document.getElementById('editMemberModal')).show();
}

document.getElementById('editMembershipType').addEventListener('change', (e) => {
    document.getElementById('editTimedOptions').classList.toggle('d-none', e.target.value !== 'timed');
    document.getElementById('editCreditOptions').classList.toggle('d-none', e.target.value !== 'credit');
});

document.getElementById('confirmEditMember').addEventListener('click', async () => {
    const membershipId = document.getElementById('editMembershipId').value;
    const type = document.getElementById('editMembershipType').value;
    const days = document.getElementById('editMemberDays').value;
    const creditTotal = document.getElementById('editCreditTotal').value;
    const isActive = document.getElementById('editMemberStatus').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/membership/${membershipId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type,
                days: type === 'timed' ? parseInt(days) : null,
                credits: type === 'credit' ? parseInt(creditTotal) : null,
                is_active: parseInt(isActive)
            })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editMemberModal')).hide();
            showAlert('Üyelik güncellendi! ✅', 'success');
            loadMembers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Güncelleme başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// Add Credit Modal
function openAddCreditModal(membershipId, name, type) {
    document.getElementById('creditMembershipId').value = membershipId;
    document.getElementById('creditMemberName').value = name;
    document.getElementById('creditHint').textContent = type === 'timed' ? 'Gün sayısı' : 'Giriş hakkı';
    document.getElementById('creditAmount').value = 30;
    new bootstrap.Modal(document.getElementById('addCreditModal')).show();
}

document.getElementById('confirmAddCredit').addEventListener('click', async () => {
    const membershipId = document.getElementById('creditMembershipId').value;
    const amount = document.getElementById('creditAmount').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/membership/${membershipId}/add-credit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: parseInt(amount) })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addCreditModal')).hide();
            showAlert('Bakiye eklendi! ✅', 'success');
            loadMembers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'İşlem başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// ==================== TRAINERS ====================
async function loadTrainers() {
    try {
        const response = await fetch(`${API_BASE}/trainers?gym_id=${currentGymId}`);
        if (response.ok) {
            allTrainers = await response.json();
            renderTrainersTable(allTrainers);
            renderTrainersList(allTrainers);
            document.getElementById('statTotalTrainers').textContent = allTrainers.length;
        }
    } catch (error) {
        console.log('Trainers error:', error);
    }
}

function renderTrainersTable(trainers) {
    const tbody = document.getElementById('allTrainersTable');
    if (trainers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4">Henüz antrenör yok</td></tr>';
        return;
    }
    
    tbody.innerHTML = trainers.map(t => `
        <tr>
            <td>#${t.trainer_id}</td>
            <td>${t.name}</td>
            <td>${t.specialty || '-'}</td>
            <td>⭐ ${t.rating_avg || '-'}</td>
            <td><span class="badge ${t.is_in_gym ? 'badge-active' : 'badge-inactive'}">${t.is_in_gym ? 'Evet' : 'Hayır'}</span></td>
            <td>${t.member_id ? `<span class="badge bg-info">#${t.member_id}</span>` : '<span class="text-muted">-</span>'}</td>
            <td>
                <button class="btn btn-warning action-btn" onclick="openEditTrainerModal(${t.trainer_id}, '${t.name}', '${t.specialty || ''}', ${t.is_in_gym ? 1 : 0}, ${t.member_id || 'null'})" title="Düzenle">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-danger action-btn" onclick="openDeleteModal(${t.trainer_id}, 'trainer', '${t.name}')" title="Sil">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderTrainersList(trainers) {
    const container = document.getElementById('trainersList');
    if (trainers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">Henüz antrenör yok</p>';
        return;
    }
    
    container.innerHTML = trainers.slice(0, 4).map(t => `
        <div class="trainer-card">
            <div class="trainer-avatar"><i class="bi bi-person"></i></div>
            <div class="trainer-info">
                <h6>${t.name}</h6>
                <small>${t.specialty || '-'}</small>
            </div>
            <span class="badge ${t.is_in_gym ? 'badge-active' : 'badge-inactive'}">${t.is_in_gym ? 'Salonda' : 'Dışarıda'}</span>
        </div>
    `).join('');
}

// Add Trainer
function populateMemberDropdown(selectId, selectedMemberId = null) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">-- Mevcut üye seçin (opsiyonel) --</option>';
    
    // Zaten trainer olan üyeleri bul
    const trainerMemberIds = allTrainers.map(t => t.member_id).filter(id => id !== null);
    
    allMembers.forEach(m => {
        // Sadece aktif üyeleri listele ve zaten trainer olmayanları
        if (m.is_active && (!trainerMemberIds.includes(m.member_id) || m.member_id === selectedMemberId)) {
            const option = document.createElement('option');
            option.value = m.member_id;
            option.textContent = `${m.name} (${m.email})`;
            if (m.member_id === selectedMemberId) {
                option.selected = true;
            }
            select.appendChild(option);
        }
    });
}

// Üye seçilince adını otomatik doldur
document.getElementById('trainerMemberId').addEventListener('change', (e) => {
    if (e.target.value) {
        const member = allMembers.find(m => m.member_id == e.target.value);
        if (member) {
            document.getElementById('trainerName').value = member.name;
        }
    }
});

// Modal açılınca üyeleri yükle
document.getElementById('addTrainerModal').addEventListener('show.bs.modal', () => {
    populateMemberDropdown('trainerMemberId');
});

document.getElementById('confirmAddTrainer').addEventListener('click', async () => {
    const name = document.getElementById('trainerName').value;
    const specialty = document.getElementById('trainerSpecialty').value;
    const memberId = document.getElementById('trainerMemberId').value;
    
    if (!name || !specialty) {
        showAlert('Tüm alanları doldurun!', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/trainers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gym_id: currentGymId,
                name,
                specialty,
                member_id: memberId ? parseInt(memberId) : null
            })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addTrainerModal')).hide();
            document.getElementById('trainerName').value = '';
            document.getElementById('trainerSpecialty').value = '';
            document.getElementById('trainerMemberId').value = '';
            showAlert('Antrenör eklendi! 🎉', 'success');
            loadTrainers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Antrenör eklenemedi', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// Edit Trainer
function openEditTrainerModal(trainerId, name, specialty, isInGym, memberId) {
    document.getElementById('editTrainerId').value = trainerId;
    document.getElementById('editTrainerName').value = name;
    document.getElementById('editTrainerSpecialty').value = specialty;
    document.getElementById('editTrainerInGym').value = isInGym;
    
    // Üye dropdown'ını doldur ve seçili üyeyi işaretle
    populateMemberDropdown('editTrainerMemberId', memberId);
    
    new bootstrap.Modal(document.getElementById('editTrainerModal')).show();
}

document.getElementById('editTrainerMemberId').addEventListener('change', (e) => {
    if (e.target.value) {
        const member = allMembers.find(m => m.member_id == e.target.value);
        if (member) {
            document.getElementById('editTrainerName').value = member.name;
        }
    }
});

document.getElementById('confirmEditTrainer').addEventListener('click', async () => {
    const trainerId = document.getElementById('editTrainerId').value;
    const name = document.getElementById('editTrainerName').value;
    const specialty = document.getElementById('editTrainerSpecialty').value;
    const isInGym = document.getElementById('editTrainerInGym').value;
    const memberId = document.getElementById('editTrainerMemberId').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/trainers/${trainerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name, 
                specialty, 
                is_in_gym: parseInt(isInGym),
                member_id: memberId ? parseInt(memberId) : null
            })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editTrainerModal')).hide();
            showAlert('Antrenör güncellendi! ✅', 'success');
            loadTrainers();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Güncelleme başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// ==================== DELETE ====================
function openDeleteModal(itemId, itemType, itemName) {
    document.getElementById('deleteItemId').value = itemId;
    document.getElementById('deleteItemType').value = itemType;
    document.getElementById('deleteMessage').textContent = `"${itemName}" silinecek. Emin misiniz?`;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

document.getElementById('confirmDelete').addEventListener('click', async () => {
    const itemId = document.getElementById('deleteItemId').value;
    const itemType = document.getElementById('deleteItemType').value;
    
    let endpoint;
    if (itemType === 'member') {
        endpoint = `${API_BASE}/admin/membership/${itemId}`;
    } else if (itemType === 'trainer') {
        endpoint = `${API_BASE}/admin/trainers/${itemId}`;
    } else if (itemType === 'program') {
        endpoint = `${API_BASE}/admin/programs/${itemId}`;
    }
    
    try {
        const response = await fetch(endpoint, { method: 'DELETE' });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
            showAlert('Silindi! 🗑️', 'success');
            if (itemType === 'member') {
                loadMembers();
                loadStats();
            } else if (itemType === 'trainer') {
                loadTrainers();
            } else if (itemType === 'program') {
                loadPrograms();
            }
        } else {
            const data = await response.json();
            showAlert(data.error || 'Silme başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// ==================== PROGRAMS ====================
async function loadPrograms() {
    try {
        const response = await fetch(`${API_BASE}/admin/programs?gym_id=${currentGymId}`);
        if (response.ok) {
            allPrograms = await response.json();
            renderProgramsTable(allPrograms);
        }
    } catch (error) {
        console.log('Programs error:', error);
    }
}

async function loadExercises() {
    try {
        const response = await fetch(`${API_BASE}/exercises`);
        if (response.ok) {
            allExercises = await response.json();
        }
    } catch (error) {
        console.log('Exercises error:', error);
    }
}

function renderProgramsTable(programs) {
    const tbody = document.getElementById('allProgramsTable');
    if (programs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4">Henüz program yok</td></tr>';
        return;
    }
    
    tbody.innerHTML = programs.map(p => `
        <tr>
            <td>#${p.fixed_id}</td>
            <td>${p.title}</td>
            <td>${p.duration_min} dk</td>
            <td><span class="badge bg-primary">${p.exercise_count || 0} egzersiz</span></td>
            <td>
                <button class="btn btn-info action-btn" onclick="openProgramExercisesModal(${p.fixed_id}, '${p.title}')" title="Egzersizler">
                    <i class="bi bi-list-ul"></i>
                </button>
                <button class="btn btn-warning action-btn" onclick="openEditProgramModal(${p.fixed_id}, '${p.title}', ${p.duration_min})" title="Düzenle">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-danger action-btn" onclick="openDeleteModal(${p.fixed_id}, 'program', '${p.title}')" title="Sil">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Add Program
document.getElementById('confirmAddProgram').addEventListener('click', async () => {
    const title = document.getElementById('programTitle').value;
    const durationMin = document.getElementById('programDuration').value;
    
    if (!title) {
        showAlert('Program adı gerekli!', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/programs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gym_id: currentGymId,
                title,
                duration_min: parseInt(durationMin)
            })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addProgramModal')).hide();
            document.getElementById('programTitle').value = '';
            document.getElementById('programDuration').value = '45';
            showAlert('Program eklendi! 🎉', 'success');
            loadPrograms();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Program eklenemedi', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// Edit Program
function openEditProgramModal(programId, title, durationMin) {
    document.getElementById('editProgramId').value = programId;
    document.getElementById('editProgramTitle').value = title;
    document.getElementById('editProgramDuration').value = durationMin;
    new bootstrap.Modal(document.getElementById('editProgramModal')).show();
}

document.getElementById('confirmEditProgram').addEventListener('click', async () => {
    const programId = document.getElementById('editProgramId').value;
    const title = document.getElementById('editProgramTitle').value;
    const durationMin = document.getElementById('editProgramDuration').value;
    
    try {
        const response = await fetch(`${API_BASE}/admin/programs/${programId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, duration_min: parseInt(durationMin) })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editProgramModal')).hide();
            showAlert('Program güncellendi! ✅', 'success');
            loadPrograms();
        } else {
            const data = await response.json();
            showAlert(data.error || 'Güncelleme başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

// Program Exercises Modal
let currentProgramId = null;

async function openProgramExercisesModal(programId, programTitle) {
    currentProgramId = programId;
    document.getElementById('programExercisesTitle').textContent = `${programTitle} - Egzersizler`;
    
    // Egzersiz dropdown'ını doldur
    populateExerciseDropdown();
    
    // Mevcut egzersizleri yükle
    await loadProgramExercises(programId);
    
    new bootstrap.Modal(document.getElementById('programExercisesModal')).show();
}

function populateExerciseDropdown() {
    const select = document.getElementById('newExerciseId');
    select.innerHTML = '<option value="">-- Egzersiz seçin --</option>';
    
    // Kas gruplarına göre sırala ve düz liste yap
    const sorted = [...allExercises].sort((a, b) => {
        if (a.muscle_group === b.muscle_group) {
            return a.name.localeCompare(b.name);
        }
        return a.muscle_group.localeCompare(b.muscle_group);
    });
    
    sorted.forEach(e => {
        const option = document.createElement('option');
        option.value = e.exercise_id;
        option.textContent = `${e.name} (${e.muscle_group})`;
        select.appendChild(option);
    });
}

async function loadProgramExercises(programId) {
    try {
        const response = await fetch(`${API_BASE}/admin/programs/${programId}/exercises`);
        if (response.ok) {
            const exercises = await response.json();
            renderProgramExercises(exercises);
        }
    } catch (error) {
        console.log('Program exercises error:', error);
    }
}

function renderProgramExercises(exercises) {
    const container = document.getElementById('programExercisesList');
    if (exercises.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">Bu programda henüz egzersiz yok</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>Sıra</th>
                    <th>Egzersiz</th>
                    <th>Kas Grubu</th>
                    <th>Set</th>
                    <th>Tekrar</th>
                    <th>Dinlenme</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                ${exercises.map(e => `
                    <tr>
                        <td>${e.order_no}</td>
                        <td>${e.name}</td>
                        <td><span class="badge bg-secondary">${e.muscle_group}</span></td>
                        <td>${e.sets}</td>
                        <td>${e.reps}</td>
                        <td>${e.rest_sec}s</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="removeExerciseFromProgram(${e.exercise_id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Add Exercise to Program
document.getElementById('addExerciseBtn').addEventListener('click', async () => {
    const exerciseId = document.getElementById('newExerciseId').value;
    const sets = document.getElementById('newExerciseSets').value;
    const reps = document.getElementById('newExerciseReps').value;
    const restSec = document.getElementById('newExerciseRest').value;
    
    if (!exerciseId) {
        showAlert('Egzersiz seçin!', 'danger');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/programs/${currentProgramId}/exercises`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                exercise_id: parseInt(exerciseId),
                sets: parseInt(sets),
                reps: parseInt(reps),
                rest_sec: parseInt(restSec)
            })
        });
        
        if (response.ok) {
            document.getElementById('newExerciseId').value = '';
            showAlert('Egzersiz eklendi!', 'success');
            await loadProgramExercises(currentProgramId);
            loadPrograms(); // Egzersiz sayısını güncelle
        } else {
            const data = await response.json();
            showAlert(data.error || 'Egzersiz eklenemedi', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
});

async function removeExerciseFromProgram(exerciseId) {
    if (!confirm('Bu egzersizi programdan kaldırmak istediğinize emin misiniz?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/programs/${currentProgramId}/exercises/${exerciseId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('Egzersiz kaldırıldı!', 'success');
            await loadProgramExercises(currentProgramId);
            loadPrograms(); // Egzersiz sayısını güncelle
        } else {
            const data = await response.json();
            showAlert(data.error || 'İşlem başarısız', 'danger');
        }
    } catch (error) {
        showAlert('Sunucu hatası', 'danger');
    }
}

// ==================== NAVIGATION ====================
function navigateTo(page) {
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${page}`).classList.add('active');
    
    const titles = { 'dashboard': 'Dashboard', 'members': 'Üyeler', 'trainers': 'Antrenörler', 'programs': 'Programlar', 'settings': 'Ayarlar' };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';
}

document.querySelectorAll('.nav-link[data-page]').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(e.target.closest('.nav-link').dataset.page);
    });
});

// ==================== LOGOUT ====================
document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('gymId');
    localStorage.removeItem('adminUsername');
    currentGymId = null;
    currentAdminUsername = null;
    
    document.getElementById('dashboardPage').classList.add('d-none');
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('loginForm').reset();
});

// ==================== UTILITY ====================
function showAlert(message, type) {
    document.getElementById('alertContainer').innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    setTimeout(() => {
        const alert = document.querySelector('#alertContainer .alert');
        if (alert) alert.remove();
    }, 5000);
}

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    const savedGymId = localStorage.getItem('gymId');
    const savedUsername = localStorage.getItem('adminUsername');
    if (savedGymId) {
        currentGymId = parseInt(savedGymId);
        currentAdminUsername = savedUsername;
        showDashboard();
    }
});
