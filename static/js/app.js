// --- APPLICATION STATE ---
const appState = {
    currentPage: 'home',
    selectedLocation: null,
    selectedDate: null,
    selectedMonth: null,
    selectedYear: null,
    selectedPeople: { adults: 1, children: 0 },
    flightToBook: null,
    bookedFlight: null,
    liveFactors: { seasonality: 0, demand: 0, competition: 0 },
    priceForecast: [],
    userName: 'Bittu Jaiswal',
    userMobile: '+91 7992414122',
    userEmail: 'jaiswalbittu462@gmail.com',
    isVerified: true,
    userBookings: [],
    pendingAuth: {
        identifier: '',
        email: '',
        otp: ''
    }
};

// --- TOAST NOTIFICATIONS ---
function showToast(message, icon = '✈️') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');
    if (!toast) return;

    toastMsg.textContent = message;
    toastIcon.textContent = icon;
    toast.classList.remove('translate-y-24', 'opacity-0', 'pointer-events-none');
    
    setTimeout(() => {
        toast.classList.add('translate-y-24', 'opacity-0', 'pointer-events-none');
    }, 3500);
}

// --- MODAL CONTROLS ---
const modalOverlay = document.getElementById('modal-overlay');

function openModal(modalId) {
    closeModal();
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modalOverlay.classList.remove('hidden');
    modal.classList.remove('hidden');
    if (modalId === 'login-modal') {
        backToAuthMain();
    }
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => modal.classList.add('hidden'));
    modalOverlay.classList.add('hidden');
}

if (modalOverlay) {
    modalOverlay.addEventListener('click', closeModal);
}

// --- AUTHENTICATION & MULTI-FACTOR RESEND CONTROLS ---
function switchAuthTab(tab) {
    const tabLogin = document.getElementById('auth-tab-login');
    const tabSignup = document.getElementById('auth-tab-signup');
    const panelLogin = document.getElementById('auth-panel-login');
    const panelSignup = document.getElementById('auth-panel-signup');

    if (tab === 'login') {
        tabLogin.className = "flex-1 py-2.5 text-center font-bold text-sm rounded-xl bg-white text-blue-600 shadow-sm transition-all";
        tabSignup.className = "flex-1 py-2.5 text-center font-bold text-sm rounded-xl text-gray-500 hover:text-gray-800 transition-all";
        panelLogin.classList.remove('hidden');
        panelSignup.classList.add('hidden');
    } else {
        tabSignup.className = "flex-1 py-2.5 text-center font-bold text-sm rounded-xl bg-white text-blue-600 shadow-sm transition-all";
        tabLogin.className = "flex-1 py-2.5 text-center font-bold text-sm rounded-xl text-gray-500 hover:text-gray-800 transition-all";
        panelSignup.classList.remove('hidden');
        panelLogin.classList.add('hidden');
    }
}

function backToAuthMain() {
    const mainView = document.getElementById('auth-main-view');
    const otpView = document.getElementById('auth-otp-view');
    if (mainView && otpView) {
        mainView.classList.remove('hidden');
        otpView.classList.add('hidden');
    }
}

function showOtpView(identifier, email, devOtp) {
    const mainView = document.getElementById('auth-main-view');
    const otpView = document.getElementById('auth-otp-view');
    const targetDisplay = document.getElementById('otp-target-display');
    const devCodeDisplay = document.getElementById('otp-dev-code');
    const otpInput = document.getElementById('otp-code-input');

    appState.pendingAuth.identifier = identifier;
    appState.pendingAuth.email = email;
    appState.pendingAuth.otp = devOtp || '';

    if (targetDisplay) targetDisplay.textContent = `${identifier} (${email})`;
    if (devCodeDisplay) devCodeDisplay.textContent = devOtp || 'Sent to Mail';
    if (otpInput) {
        otpInput.value = '';
        setTimeout(() => otpInput.focus(), 200);
    }

    if (mainView && otpView) {
        mainView.classList.add('hidden');
        otpView.classList.remove('hidden');
    }
}

function togglePasswordVisibility(inputId, toggleEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        if (toggleEl) toggleEl.textContent = 'Hide';
    } else {
        input.type = 'password';
        if (toggleEl) toggleEl.textContent = 'Show';
    }
}

function autoFillDevOtp() {
    const otpInput = document.getElementById('otp-code-input');
    if (otpInput && appState.pendingAuth.otp) {
        otpInput.value = appState.pendingAuth.otp;
        showToast("Auto-filled verification OTP code!", "⚡");
    }
}

async function handleLoginSubmit(skipOtp = false) {
    const identifier = document.getElementById('login-id-input').value.trim();
    const password = document.getElementById('login-pwd-input').value.trim();

    if (!identifier || !password) {
        showToast("Please provide mobile number/email and password", "⚠️");
        return;
    }

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier, password, skip_otp: skipOtp })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Login failed");
        }

        if (data.direct_login) {
            loginUser(false, data.user);
            showToast("Directly authenticated! (Resend token saved)", "⚡");
        } else {
            showToast(data.message, "📩");
            showOtpView(data.identifier, data.email, data.dev_otp);
        }
    } catch (err) {
        showToast(err.message, "❌");
    }
}

async function handleSignupSubmit(skipOtp = false) {
    const name = document.getElementById('signup-name-input').value.trim();
    const mobile = document.getElementById('signup-mobile-input').value.trim();
    const email = document.getElementById('signup-email-input').value.trim();
    const password = document.getElementById('signup-pwd-input').value.trim();

    if (!name || !mobile || !email || !password) {
        showToast("All fields are required for registration", "⚠️");
        return;
    }

    try {
        const res = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, mobile, email, password, skip_otp: skipOtp })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Registration failed");
        }

        if (data.direct_login) {
            loginUser(false, data.user);
            showToast("Account saved in database and logged in!", "🎉");
        } else {
            showToast(data.message, "📩");
            showOtpView(data.identifier, data.email, data.dev_otp);
        }
    } catch (err) {
        showToast(err.message, "❌");
    }
}

async function handleVerifyOtpSubmit() {
    const otpCode = document.getElementById('otp-code-input').value.trim();
    if (!otpCode || otpCode.length !== 6) {
        showToast("Please enter the 6-digit OTP code", "⚠️");
        return;
    }

    try {
        const res = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                identifier: appState.pendingAuth.identifier,
                otp_code: otpCode
            })
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Invalid or expired OTP");
        }

        loginUser(false, data.user);
        showToast("Multi-Factor Authentication verified!", "✅");
    } catch (err) {
        showToast(err.message, "❌");
    }
}

async function handleResendOtp() {
    if (!appState.pendingAuth.identifier) return;
    try {
        const res = await fetch('/api/auth/resend-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: appState.pendingAuth.identifier })
        });
        const data = await res.json();
        if (data.success) {
            appState.pendingAuth.otp = data.dev_otp;
            const devCodeDisplay = document.getElementById('otp-dev-code');
            if (devCodeDisplay) devCodeDisplay.textContent = data.dev_otp;
            showToast("New OTP dispatched via Resend", "📨");
        }
    } catch (err) {
        showToast("Failed to resend code", "⚠️");
    }
}

async function handleOneClickDemoLogin() {
    try {
        const res = await fetch('/api/auth/direct-demo-login', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            loginUser(false, data.user);
            showToast("Logged in as Demo User (Bittu Jaiswal)", "⚡");
        }
    } catch (err) {
        loginUser(true);
    }
}

async function openUsersDbModal() {
    openModal('users-db-modal');
    const container = document.getElementById('users-db-table-container');
    if (!container) return;
    container.innerHTML = `<p class="text-center text-gray-400 py-6">Querying SQLite database...</p>`;
    
    try {
        const res = await fetch('/api/auth/users');
        const data = await res.json();
        const users = data.users || [];
        
        if (users.length === 0) {
            container.innerHTML = `<p class="text-center text-gray-400 py-6">No user records found in SQLite.</p>`;
            return;
        }

        let html = `
            <table class="w-full text-left border-collapse border border-gray-100 rounded-xl overflow-hidden">
                <thead>
                    <tr class="bg-slate-50 text-gray-600 font-bold border-b">
                        <th class="p-2.5">ID</th>
                        <th class="p-2.5">Name</th>
                        <th class="p-2.5">Mobile</th>
                        <th class="p-2.5">Email</th>
                        <th class="p-2.5">2FA Verified</th>
                        <th class="p-2.5">Registered At</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
        `;
        users.forEach(u => {
            html += `
                <tr class="hover:bg-blue-50/50">
                    <td class="p-2.5 font-mono text-gray-500">${u.id}</td>
                    <td class="p-2.5 font-bold text-gray-800">${u.name}</td>
                    <td class="p-2.5 font-mono text-blue-600">${u.mobile}</td>
                    <td class="p-2.5 text-gray-600">${u.email}</td>
                    <td class="p-2.5">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${u.is_verified ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}">
                            ${u.is_verified ? 'Verified ✓' : 'Pending'}
                        </span>
                    </td>
                    <td class="p-2.5 text-gray-400">${u.created_at || 'Recent'}</td>
                </tr>
            `;
        });
        html += `</tbody></table>`;
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<p class="text-center text-red-500 py-6">Failed to fetch user records.</p>`;
    }
}

function loginUser(isGuest = false, userData = null) {
    if (isGuest) {
        appState.userName = 'Guest User';
        appState.userMobile = 'N/A';
        appState.userEmail = 'guest@bookingadventures.com';
        appState.isVerified = false;
    } else if (userData) {
        appState.userName = userData.name || 'Bittu Jaiswal';
        appState.userMobile = userData.mobile || '+91 7992414122';
        appState.userEmail = userData.email || 'jaiswalbittu462@gmail.com';
        appState.isVerified = userData.is_verified === 1 || userData.is_verified === true;
    } else {
        appState.userName = 'Bittu Jaiswal';
        appState.userMobile = '+91 7992414122';
        appState.userEmail = 'jaiswalbittu462@gmail.com';
        appState.isVerified = true;
    }
    updateHeaderUI();
    closeModal();
    loadUserBookings();
}

function logoutUser() {
    appState.userName = 'Guest User';
    appState.userMobile = 'N/A';
    appState.userEmail = 'guest@bookingadventures.com';
    appState.isVerified = false;
    appState.bookedFlight = null;
    updateHeaderUI();
    renderHomePage();
    showPage('home');
    showToast('Logged out successfully', '👋');
}

function updateHeaderUI() {
    const loginBtn = document.getElementById('login-button-header');
    const profileBtn = document.getElementById('user-profile-button');
    const nameDisplay = document.getElementById('user-name-display');
    const avatar = document.getElementById('user-avatar');
    const menuEmail = document.getElementById('menu-user-email');

    if (appState.userName === 'Guest User') {
        if (loginBtn) loginBtn.classList.remove('hidden');
        if (profileBtn) profileBtn.classList.add('hidden');
    } else {
        if (loginBtn) loginBtn.classList.add('hidden');
        if (profileBtn) profileBtn.classList.remove('hidden');
        if (nameDisplay) {
            nameDisplay.innerHTML = `${appState.userName} ${appState.isVerified ? '<span class="text-blue-500 text-xs" title="2FA Verified">✓</span>' : ''}`;
        }
        if (avatar) avatar.textContent = appState.userName.charAt(0).toUpperCase();
        if (menuEmail) menuEmail.innerHTML = `<strong>${appState.userMobile}</strong><br>${appState.userEmail}`;
    }
    const profileMenu = document.getElementById('profile-menu');
    if (profileMenu) profileMenu.classList.add('hidden');
}

function toggleProfileMenu() {
    const menu = document.getElementById('profile-menu');
    if (menu) menu.classList.toggle('hidden');
}

// --- NAVIGATION & PAGE ROUTING ---
function showPage(pageId) {
    closeModal();
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    
    const newPage = document.getElementById(pageId);
    if (newPage) {
        newPage.classList.add('active', 'fade-in');
    }
    appState.currentPage = pageId;

    if (pageId === 'home') renderHomePage();
    if (pageId === 'bookings') loadUserBookings();
    if (pageId === 'analytics-lab') loadMLMetrics();

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function checkDiscoverButton() {
    const btn = document.getElementById('discover-now-btn');
    if (!btn) return;
    if (appState.selectedLocation && appState.selectedDate) {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
    }
}

// --- HOME PAGE BOARDING PASS TICKET RENDER ---
function renderHomePage() {
    const confirmationSection = document.getElementById('booking-confirmation-section');
    if (!confirmationSection) return;

    if (appState.bookedFlight) {
        const flight = appState.bookedFlight;
        const totalPassengers = appState.selectedPeople.adults + appState.selectedPeople.children;
        const seatsDisplay = Array.isArray(flight.seats) ? flight.seats.join(', ') : flight.seats;

        confirmationSection.innerHTML = `
        <div class="max-w-xl mx-auto bg-white/90 backdrop-blur-md rounded-3xl p-6 shadow-2xl border border-white">
            <div class="text-center mb-6">
                <div class="inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider mb-2">
                    <span>✓ Confirmed Booking</span>
                </div>
                <h2 class="text-3xl font-extrabold text-gray-900">Your Flight Ticket is Ready!</h2>
                <p class="text-gray-500 text-sm">Have a wonderful journey to <span class="font-bold text-blue-600">${appState.selectedLocation}</span>, ${appState.userName}!</p>
            </div>
            
            <div class="ticket max-w-md mx-auto shadow-2xl rounded-2xl overflow-hidden">
                <div class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6 relative">
                    <div class="flex justify-between items-center">
                        <span class="bg-white/20 backdrop-blur-sm text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">${flight.class || 'Economy'}</span>
                        <span class="font-mono text-xs font-bold bg-black/20 px-2.5 py-1 rounded">PNR: ${flight.pnr || 'BA' + Math.floor(1000 + Math.random()*9000)}</span>
                    </div>
                    <div class="flex justify-between items-center my-4">
                        <div>
                            <p class="text-2xl font-black">${flight.from || 'PNQ'}</p>
                            <p class="text-xs text-blue-100 font-semibold">${flight.from_name || 'Origin'}</p>
                        </div>
                        <div class="flex flex-col items-center">
                            <span class="text-xs text-blue-200">${flight.duration || '3h 30m'}</span>
                            <div class="text-xl">✈️</div>
                            <span class="text-[10px] text-blue-200">Non-stop</span>
                        </div>
                        <div class="text-right">
                            <p class="text-2xl font-black">${flight.to || 'DEL'}</p>
                            <p class="text-xs text-blue-100 font-semibold">${flight.to_name || appState.selectedLocation}</p>
                        </div>
                    </div>
                    <p class="text-sm font-semibold">${totalPassengers > 1 ? `${totalPassengers} Passengers` : '1 Passenger'} &bull; ${flight.airline || flight.name}</p>
                </div>
                
                <div class="bg-white p-6 relative">
                    <div class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Passenger</p><p class="font-bold text-gray-800">${appState.userName}</p></div>
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Date</p><p class="font-bold text-gray-800">${appState.selectedDate || 'Upcoming'} ${getMonthName(appState.selectedMonth)} ${appState.selectedYear || '2026'}</p></div>
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Flight</p><p class="font-bold text-gray-800">${flight.flightNumber || flight.flight_number}</p></div>
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Gate</p><p class="font-bold text-gray-800">${flight.gate || 'B4'}</p></div>
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Seats</p><p class="font-bold text-blue-600">${seatsDisplay || 'Unassigned'}</p></div>
                        <div><p class="text-xs text-gray-400 uppercase font-semibold">Dynamic Total</p><p class="font-bold text-green-600">₹${Number(flight.price || flight.total_price).toLocaleString('en-IN')}</p></div>
                    </div>
                </div>

                <!-- Perforated Cutout Divider -->
                <div class="bg-white relative flex items-center">
                    <div class="absolute -left-4 w-8 h-8 bg-gradient-to-b from-sky-200 to-orange-100 rounded-full shadow-inner"></div>
                    <div class="w-full border-t-2 border-dashed border-gray-300"></div>
                    <div class="absolute -right-4 w-8 h-8 bg-gradient-to-b from-sky-200 to-orange-100 rounded-full shadow-inner"></div>
                </div>

                <div class="bg-white p-6 rounded-b-2xl flex flex-col items-center">
                    <div class="ticket-barcode w-full mb-3"></div>
                    <div class="flex space-x-3 w-full">
                        <button onclick="window.print()" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 px-4 rounded-xl text-xs transition-colors">
                            🖨️ Print Ticket
                        </button>
                        <button onclick="showPage('bookings')" class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-xl text-xs transition-colors">
                            View All Bookings
                        </button>
                    </div>
                </div>
            </div>
        </div>`;
        confirmationSection.classList.remove('hidden');
    } else {
        confirmationSection.classList.add('hidden');
    }
}

function getMonthName(m) {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[m] || "Nov";
}

// --- CALENDAR LOGIC ---
function renderCalendar() {
    const container = document.getElementById('calendar-container');
    if (!container) return;

    container.innerHTML = `
    <div class="flex justify-between items-center mb-4">
        <h4 class="font-bold text-gray-700">Select Date in Upcoming Season (2026-2027)</h4>
        <span class="text-xs text-blue-600 font-semibold bg-blue-50 px-3 py-1 rounded-full">Dates update live seasonality factor</span>
    </div>`;

    const gridContainer = document.createElement('div');
    gridContainer.className = 'grid grid-cols-1 md:grid-cols-3 gap-6';

    const months = [
        { m: 10, y: 2026, name: "November 2026" },
        { m: 11, y: 2026, name: "December 2026" },
        { m: 0, y: 2027, name: "January 2027" }
    ];

    months.forEach(({ m, y, name }) => {
        const monthCard = document.createElement('div');
        monthCard.className = 'bg-gray-50 p-4 rounded-2xl border border-gray-100';

        const monthHeader = document.createElement('h5');
        monthHeader.className = 'font-bold text-center text-sm text-gray-800 mb-3';
        monthHeader.textContent = name;
        monthCard.appendChild(monthHeader);

        const monthGrid = document.createElement('div');
        monthGrid.className = 'grid grid-cols-7 gap-1 text-center text-xs';
        monthGrid.innerHTML = `
            <span class="text-gray-400 font-bold">M</span>
            <span class="text-gray-400 font-bold">T</span>
            <span class="text-gray-400 font-bold">W</span>
            <span class="text-gray-400 font-bold">T</span>
            <span class="text-gray-400 font-bold">F</span>
            <span class="text-gray-400 font-bold">S</span>
            <span class="text-gray-400 font-bold">S</span>
        `;

        const firstDay = (new Date(y, m, 1).getDay() + 6) % 7;
        const daysInMonth = new Date(y, m + 1, 0).getDate();

        for (let i = 0; i < firstDay; i++) {
            monthGrid.innerHTML += `<span></span>`;
        }

        for (let i = 1; i <= daysInMonth; i++) {
            const dayEl = document.createElement('span');
            dayEl.className = 'date p-2 cursor-pointer hover:bg-blue-200 rounded-full transition-all font-medium text-gray-700';
            dayEl.textContent = i;
            dayEl.dataset.date = i;
            dayEl.dataset.month = m;
            dayEl.dataset.year = y;

            dayEl.addEventListener('click', (e) => {
                document.querySelectorAll('.date').forEach(d => {
                    d.classList.remove('bg-blue-600', 'text-white', 'font-bold');
                });
                e.target.classList.add('bg-blue-600', 'text-white', 'font-bold');
                appState.selectedDate = e.target.dataset.date;
                appState.selectedMonth = parseInt(e.target.dataset.month);
                appState.selectedYear = parseInt(e.target.dataset.year);

                const selectBtn = document.getElementById('select-date-btn');
                if (selectBtn) {
                    selectBtn.disabled = false;
                    selectBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
            });
            monthGrid.appendChild(dayEl);
        }
        monthCard.appendChild(monthGrid);
        gridContainer.appendChild(monthCard);
    });

    container.appendChild(gridContainer);
}

// --- COUNTRIES & DESTINATIONS LIST ---
const countriesData = [
    { name: "Brazil", code: "br", airport: "GIG" },
    { name: "United States", code: "us", airport: "JFK" },
    { name: "Turkey", code: "tr", airport: "IST" },
    { name: "Egypt", code: "eg", airport: "CAI" },
    { name: "United Kingdom", code: "gb", airport: "LHR" },
    { name: "Canada", code: "ca", airport: "YYZ" },
    { name: "Ireland", code: "ie", airport: "DUB" },
    { name: "Finland", code: "fi", airport: "HEL" },
    { name: "Italy", code: "it", airport: "FCO" },
    { name: "France", code: "fr", airport: "CDG" },
    { name: "Russia", code: "ru", airport: "SVO" },
    { name: "Germany", code: "de", airport: "FRA" },
    { name: "South Korea", code: "kr", airport: "ICN" },
    { name: "Argentina", code: "ar", airport: "EZE" },
    { name: "Australia", code: "au", airport: "SYD" },
    { name: "China", code: "cn", airport: "PEK" },
    { name: "Saudi Arabia", code: "sa", airport: "RUH" },
    { name: "Japan", code: "jp", airport: "NRT" },
    { name: "Bahrain", code: "bh", airport: "BAH" },
    { name: "Swaziland", code: "sz", airport: "SHO" }
];

function renderCountriesList(filtered = null) {
    const countryList = document.getElementById('country-list');
    if (!countryList) return;
    countryList.innerHTML = '';

    const list = filtered || countriesData;
    list.forEach(country => {
        const countryEl = document.createElement('div');
        countryEl.className = 'flex items-center space-x-3 p-3 rounded-xl hover:bg-blue-50 cursor-pointer border border-transparent transition-all';
        countryEl.innerHTML = `
            <img src="https://flagcdn.com/32x24/${country.code}.png" alt="${country.name} flag" class="rounded shadow-sm">
            <div>
                <p class="font-bold text-gray-800 text-sm">${country.name}</p>
                <p class="text-[10px] text-gray-400 font-semibold">${country.airport}</p>
            </div>
        `;
        countryEl.addEventListener('click', () => {
            document.querySelectorAll('#country-list > div').forEach(c => c.classList.remove('bg-blue-100', 'border-blue-500'));
            countryEl.classList.add('bg-blue-100', 'border-blue-500');
            appState.selectedLocation = country.name;

            const selectBtn = document.getElementById('select-location-btn');
            if (selectBtn) {
                selectBtn.disabled = false;
                selectBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        });
        countryList.appendChild(countryEl);
    });
}

function filterCountries() {
    const term = document.getElementById('country-search-input').value.toLowerCase();
    const filtered = countriesData.filter(c => c.name.toLowerCase().includes(term) || c.airport.toLowerCase().includes(term));
    renderCountriesList(filtered);
}

// --- FULL-STACK DYNAMIC PRICING ENGINE SEARCH ---
async function runAiAnalysis() {
    openModal('ai-modal');

    // Trigger AI loading animation steps
    document.querySelectorAll('.ai-step').forEach(el => {
        el.classList.remove('ai-step');
        void el.offsetWidth;
        el.classList.add('ai-step');
    });

    ['data-source-1', 'data-source-2', 'data-source-3', 'data-source-4'].forEach((id, i) => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('text-green-600');
            el.classList.add('text-gray-400');
            setTimeout(() => {
                el.classList.remove('text-gray-400');
                el.classList.add('text-green-600');
            }, 350 * (i + 1));
        }
    });

    try {
        const dateString = `${appState.selectedYear}-${String(appState.selectedMonth + 1).padStart(2, '0')}-${String(appState.selectedDate).padStart(2, '0')}`;
        
        // Live API call to FastAPI backend ML Pricing Engine
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destination: appState.selectedLocation,
                travel_date: dateString,
                adults: appState.selectedPeople.adults,
                children: appState.selectedPeople.children,
                cabin_class: 'Economy'
            })
        });

        if (!res.ok) {
            throw new Error('Failed to compute dynamic prices.');
        }

        const data = await res.json();
        appState.liveFactors = data.factors;
        appState.priceForecast = data.forecast;

        // Animate modal progress bars
        setTimeout(() => {
            ['seasonality', 'demand', 'competition'].forEach(factor => {
                const value = appState.liveFactors[factor];
                const modalBar = document.getElementById(`modal-${factor}-bar`);
                const modalVal = document.getElementById(`modal-${factor}-value`);
                if (modalBar) modalBar.style.width = `${value}%`;
                if (modalVal) modalVal.innerText = `${value}%`;
            });

            // Transition to results page
            setTimeout(() => {
                renderResults(data.flights);
                showPage('results');
            }, 1200);
        }, 800);

    } catch (err) {
        console.error(err);
        showToast("Error connecting to pricing engine. Using backup calculation.", "⚠️");
        closeModal();
    }
}

// --- RENDER FLIGHT SEARCH RESULTS ---
function renderResults(flights) {
    const destTitle = document.getElementById('destination-title');
    if (destTitle) destTitle.innerText = appState.selectedLocation;

    // Update factor bars in sidebar
    ['seasonality', 'demand', 'competition'].forEach(factor => {
        const val = appState.liveFactors[factor] || 50;
        const bar = document.getElementById(`${factor}-bar`);
        const text = document.getElementById(`${factor}-value`);
        if (bar) bar.style.width = `${val}%`;
        if (text) text.innerText = `${val}%`;
    });

    renderPriceForecastChart();

    const listingsContainer = document.getElementById('flight-listings');
    if (!listingsContainer) return;
    listingsContainer.innerHTML = '';

    if (!flights || flights.length === 0) {
        listingsContainer.innerHTML = `<div class="p-8 text-center text-gray-500 bg-white rounded-2xl">No flights found.</div>`;
        return;
    }

    flights.forEach(flight => {
        const isBusiness = flight.class === 'Business';
        let dealBadgeColor = 'bg-gray-100 text-gray-700';
        if (flight.deal.text === 'Excellent Deal') dealBadgeColor = 'bg-green-100 text-green-700';
        else if (flight.deal.text === 'Good Deal') dealBadgeColor = 'bg-blue-100 text-blue-700';

        let riskColor = 'text-green-600';
        if (flight.risk > 10) riskColor = 'text-red-500';
        else if (flight.risk > 5) riskColor = 'text-amber-500';

        const card = document.createElement('div');
        card.className = `bg-white p-5 rounded-2xl shadow-md grid grid-cols-1 md:grid-cols-12 gap-4 items-center fade-in transition-all hover:shadow-lg ${
            isBusiness ? 'border-2 border-purple-500/80 bg-gradient-to-r from-purple-50/40 to-white' : 'border border-gray-100'
        }`;

        card.innerHTML = `
            <!-- Airline Logo & Name -->
            <div class="col-span-12 md:col-span-2 flex md:flex-col items-center justify-between md:justify-center text-center">
                <div class="w-12 h-12 bg-slate-900 text-white rounded-xl flex items-center justify-center font-black text-base shadow-sm">
                    ${flight.logo}
                </div>
                <div class="md:mt-2 text-right md:text-center">
                    <p class="font-bold text-gray-800 text-sm">${flight.name}</p>
                    <p class="text-[10px] text-gray-400 font-mono">${flight.flight_number || flight.flightNumber}</p>
                </div>
            </div>

            <!-- Departure -->
            <div class="col-span-4 md:col-span-3 text-center">
                <p class="font-black text-2xl text-gray-800">${flight.departure}</p>
                <p class="text-xs text-gray-500 font-bold">${flight.from} <span class="text-[10px] text-gray-400">(${flight.from_name || 'Origin'})</span></p>
            </div>

            <!-- Route Duration & Icon -->
            <div class="col-span-4 md:col-span-2 text-center">
                <span class="text-xs text-gray-400 font-semibold">${flight.duration}</span>
                <div class="flex items-center justify-center my-1 text-blue-500">
                    <div class="w-8 border-t border-gray-300"></div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="mx-1"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>
                    <div class="w-8 border-t border-gray-300"></div>
                </div>
                <span class="text-[10px] text-green-600 font-bold uppercase">Direct</span>
            </div>

            <!-- Arrival -->
            <div class="col-span-4 md:col-span-3 text-center">
                <p class="font-black text-2xl text-gray-800">${flight.arrival}</p>
                <p class="text-xs text-gray-500 font-bold">${flight.to} <span class="text-[10px] text-gray-400">(${flight.to_name || appState.selectedLocation})</span></p>
            </div>

            <!-- Dynamic Price & Action -->
            <div class="col-span-12 md:col-span-2 text-center md:text-right space-y-1.5 pt-3 md:pt-0 border-t md:border-t-0">
                <p class="text-2xl font-black ${isBusiness ? 'text-purple-700' : 'text-blue-700'}">
                    ₹${flight.price.toLocaleString('en-IN')}
                </p>
                <div class="text-[11px] text-orange-600 font-semibold">
                    Demand Surge: +₹${flight.surcharge.toLocaleString('en-IN')}
                </div>
                <div class="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${dealBadgeColor}">
                    AI Deal: ${flight.deal.text}
                </div>
                <div class="text-[10px] font-bold ${riskColor}">
                    Disruption Risk: ${flight.risk}%
                </div>
                <button onclick='bookFlight(${JSON.stringify(flight)})' class="w-full ${
                    isBusiness ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'
                } text-white font-bold py-2.5 px-3 rounded-xl transition-colors text-xs shadow-md mt-1">
                    Book ${flight.class}
                </button>
            </div>
        `;
        listingsContainer.appendChild(card);
    });
}

// --- SEAT SELECTION WITH LIVE DATABASE MAP ---
async function bookFlight(flight) {
    appState.flightToBook = flight;
    const flightTitle = document.getElementById('seat-flight-title');
    if (flightTitle) flightTitle.innerText = `${flight.name} - ${flight.flight_number || flight.flightNumber} (${flight.class})`;

    try {
        const res = await fetch(`/api/seats/${flight.flight_id || 1}`);
        const data = await res.json();
        renderSeatMapFromData(data.seats);
    } catch (err) {
        console.warn("Using fallback seat layout:", err);
        renderFallbackSeatMap();
    }
    openModal('seat-selection-modal');
}

function renderSeatMapFromData(seatRows) {
    const seatMapContainer = document.getElementById('seat-map');
    const passengers = appState.selectedPeople.adults + appState.selectedPeople.children;
    document.getElementById('seats-to-select').textContent = passengers;
    document.getElementById('selected-seats-badge').textContent = 'None';

    const bookedLookup = {};
    if (seatRows) {
        seatRows.forEach(s => { bookedLookup[s.seat_number] = s.is_booked === 1; });
    }

    const rows = 15;
    const cols = ['A', 'B', 'C', '', 'D', 'E', 'F'];
    let mapHTML = '';

    for (let i = 1; i <= rows; i++) {
        mapHTML += '<div class="flex items-center space-x-2">';
        mapHTML += `<div class="w-6 text-center text-xs font-bold text-gray-400">${i}</div>`;
        cols.forEach(col => {
            if (col === '') {
                mapHTML += '<div class="w-6"></div>'; // Aisle
            } else {
                const seatId = `${i}${col}`;
                const isBooked = bookedLookup[seatId] || false;
                mapHTML += `<div class="seat ${isBooked ? 'booked' : 'available'}" data-seat="${seatId}" title="${seatId}">${col}</div>`;
            }
        });
        mapHTML += '</div>';
    }
    seatMapContainer.innerHTML = mapHTML;
    bindSeatSelectionEvents(passengers);
}

function renderFallbackSeatMap() {
    renderSeatMapFromData(null);
}

function bindSeatSelectionEvents(passengers) {
    const seatMapContainer = document.getElementById('seat-map');
    const confirmBtn = document.getElementById('confirm-seats-btn');
    const selectedBadge = document.getElementById('selected-seats-badge');

    confirmBtn.disabled = true;
    confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');

    seatMapContainer.querySelectorAll('.seat.available').forEach(seat => {
        seat.addEventListener('click', () => {
            const selectedSeats = seatMapContainer.querySelectorAll('.seat.selected');
            if (seat.classList.contains('selected')) {
                seat.classList.remove('selected');
            } else if (selectedSeats.length < passengers) {
                seat.classList.add('selected');
            }

            const currentSelected = seatMapContainer.querySelectorAll('.seat.selected');
            const seatNames = Array.from(currentSelected).map(s => s.dataset.seat);
            selectedBadge.textContent = seatNames.length > 0 ? seatNames.join(', ') : 'None';

            if (currentSelected.length === passengers) {
                confirmBtn.disabled = false;
                confirmBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                confirmBtn.disabled = true;
                confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');
            }
        });
    });

    confirmBtn.onclick = () => {
        if (!confirmBtn.disabled) {
            const finalSeats = [];
            seatMapContainer.querySelectorAll('.seat.selected').forEach(s => finalSeats.push(s.dataset.seat));
            appState.flightToBook.seats = finalSeats;

            setupPaymentSummary();
            showPage('payment');
        }
    };
}

// --- PAYMENT & BOOKING CONFIRMATION ---
function setupPaymentSummary() {
    const flight = appState.flightToBook;
    const passengers = appState.selectedPeople.adults + appState.selectedPeople.children;
    const summaryContainer = document.getElementById('payment-summary');
    const totalEl = document.getElementById('payment-total');

    if (!summaryContainer || !flight) return;

    summaryContainer.innerHTML = `
        <div class="space-y-4 text-gray-700 text-sm">
            <div class="flex items-center justify-between p-3 bg-blue-50 rounded-xl">
                <div>
                    <p class="font-bold text-gray-900">${flight.name} &bull; ${flight.flight_number || flight.flightNumber}</p>
                    <p class="text-xs text-blue-700">${flight.from} → ${flight.to} (${appState.selectedLocation})</p>
                </div>
                <span class="text-xs bg-blue-600 text-white font-bold px-2.5 py-1 rounded-md">${flight.class}</span>
            </div>
            <div class="flex justify-between py-1 border-b">
                <span class="text-gray-500">Travel Date</span>
                <span class="font-semibold">${appState.selectedDate} ${getMonthName(appState.selectedMonth)} ${appState.selectedYear}</span>
            </div>
            <div class="flex justify-between py-1 border-b">
                <span class="text-gray-500">Passengers</span>
                <span class="font-semibold">${passengers} (${appState.selectedPeople.adults} Adults, ${appState.selectedPeople.children} Children)</span>
            </div>
            <div class="flex justify-between py-1 border-b">
                <span class="text-gray-500">Reserved Seats</span>
                <span class="font-bold text-blue-600">${flight.seats.join(', ')}</span>
            </div>
            <div class="flex justify-between py-1 border-b">
                <span class="text-gray-500">Base Airfare</span>
                <span>₹${(flight.base_fare * passengers).toLocaleString('en-IN')}</span>
            </div>
            <div class="flex justify-between py-1 border-b text-orange-600">
                <span>AI Dynamic Surge Fee</span>
                <span>+₹${flight.surcharge.toLocaleString('en-IN')}</span>
            </div>
            ${appState.appliedOffer ? `
            <div class="flex justify-between py-1 border-b text-emerald-600 font-bold">
                <span>Promo Discount (${appState.appliedOffer.coupon_code})</span>
                <span>-₹${Number(appState.appliedOffer.discount_amount).toLocaleString('en-IN')}</span>
            </div>` : ''}
            <div class="flex justify-between py-1 text-gray-500">
                <span>Airport Taxes & GST</span>
                <span>Included</span>
            </div>

            <!-- Promo Code & Coupon Box -->
            <div class="mt-4 pt-3 border-t">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-gray-700">Promo Code & Live Offers</span>
                    <span class="text-[10px] bg-emerald-100 text-emerald-700 font-bold px-2 py-0.5 rounded-full">Save Instantly</span>
                </div>
                <div class="flex space-x-2">
                    <input id="promo-code-input" type="text" placeholder="Enter coupon code" value="${appState.appliedOffer ? appState.appliedOffer.coupon_code : ''}" class="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono uppercase outline-none focus:ring-2 focus:ring-blue-500">
                    <button onclick="applyPromoCode()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition-colors">
                        Apply
                    </button>
                </div>
                <div class="flex flex-wrap gap-1.5 mt-2">
                    <button onclick="applyPromoCode('BITTU20')" class="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all">
                        ⭐ BITTU20 (20% Off)
                    </button>
                    <button onclick="applyPromoCode('FLYHIGH15')" class="bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all">
                        ✈️ FLYHIGH15 (15% Off)
                    </button>
                    <button onclick="applyPromoCode('PBLSEM7')" class="bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-200 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all">
                        🎓 PBLSEM7 (₹2,500 Off)
                    </button>
                </div>
            </div>

            <!-- Live Airport Weather & Telemetry -->
            <div id="live-travel-telemetry" class="mt-3 p-3 bg-gradient-to-r from-sky-50 to-blue-50 rounded-2xl border border-blue-100 text-xs space-y-1">
                <div class="flex justify-between items-center text-blue-900 font-bold">
                    <span>🌤️ Live Airport Weather (${appState.selectedLocation})</span>
                    <span id="live-dest-weather" class="text-blue-600 font-semibold text-[11px]">Syncing live feed...</span>
                </div>
                <div class="flex justify-between items-center text-gray-500 text-[10px]">
                    <span>Flight Delay Risk:</span>
                    <span id="live-delay-risk" class="font-bold text-emerald-600">Low (On Schedule)</span>
                </div>
            </div>
        </div>
    `;

    if (totalEl) totalEl.innerText = `₹${flight.price.toLocaleString('en-IN')}`;

    const nameEl = document.getElementById('pay-customer-name');
    const emailEl = document.getElementById('pay-customer-email');
    const phoneEl = document.getElementById('pay-customer-phone');
    const rzpBtn = document.getElementById('razorpay-pay-btn');

    if (nameEl) nameEl.textContent = appState.userName;
    if (emailEl) emailEl.textContent = appState.userEmail;
    if (phoneEl) phoneEl.textContent = appState.userMobile;
    const keyBadge = document.getElementById('current-rzp-key');
    if (keyBadge && appState.razorpayKeyId) keyBadge.textContent = appState.razorpayKeyId;
    if (rzpBtn) rzpBtn.innerHTML = `<span>💳 Pay ₹${Number(flight.price).toLocaleString('en-IN')} with Razorpay Gateway</span>`;

    fetchLiveFlightTelemetry(appState.selectedLocation);
}

// --- LIVE PROMOTIONAL OFFERS & COUPONS ---
async function applyPromoCode(inputCode) {
    const flight = appState.flightToBook;
    if (!flight) return;

    const input = document.getElementById('promo-code-input');
    const code = inputCode || (input ? input.value.trim() : '');
    if (!code) {
        showToast("Please enter a coupon code", "⚠️");
        return;
    }

    try {
        if (!flight.originalBasePrice) {
            flight.originalBasePrice = flight.price;
        }

        const res = await fetch('/api/offers/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                coupon_code: code,
                amount: flight.originalBasePrice
            })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Invalid coupon code");
        }

        flight.price = data.final_amount;
        appState.appliedOffer = data;

        showToast(data.message, "🎉");
        setupPaymentSummary();
    } catch (err) {
        showToast(err.message, "❌");
    }
}

// --- TAVILY LIVE SEARCH & TELEMETRY ---
function openTavilyKeyModal() {
    openModal('tavily-key-modal');
}

async function saveTavilyCredentials() {
    const input = document.getElementById('custom-tavily-key');
    const key = input ? input.value.trim() : '';
    if (!key) {
        showToast("Please enter your Tavily API Key", "⚠️");
        return;
    }

    try {
        const res = await fetch('/api/live/set-tavily-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: key })
        });
        const data = await res.json();
        if (data.success) {
            closeModal();
            showToast("Tavily AI Search API Connected!", "🌐");
        }
    } catch (e) {
        console.error(e);
        showToast("Error updating Tavily key", "❌");
    }
}

async function fetchLiveForexAndTelemetry() {
    try {
        const res = await fetch('/api/live/forex');
        const data = await res.json();
        if (data.success) {
            const el = document.getElementById('header-forex-usd');
            if (el) el.textContent = `1 USD = ₹${data.usd_inr}`;
        }
    } catch (e) {
        console.warn("Live forex fetch notice:", e);
    }
}

async function fetchLiveFlightTelemetry(city) {
    try {
        const res = await fetch(`/api/live/weather/${encodeURIComponent(city || 'Dubai')}`);
        const data = await res.json();
        if (data.success) {
            const wEl = document.getElementById('live-dest-weather');
            const dEl = document.getElementById('live-delay-risk');
            if (wEl) wEl.textContent = `${data.temperature_c}°C, ${data.condition}`;
            if (dEl) {
                dEl.textContent = data.delay_risk;
                if (data.delay_risk.includes('Low')) {
                    dEl.className = 'font-bold text-emerald-600';
                } else {
                    dEl.className = 'font-bold text-amber-600';
                }
            }
        }
    } catch (e) {
        console.warn("Live weather fetch notice:", e);
    }
}

// --- REAL WORKING RAZORPAY PAYMENT GATEWAY ---
function switchRzpTab(tab) {
    const tabs = ['upi', 'card', 'netbanking', 'wallets'];
    tabs.forEach(t => {
        const tabBtn = document.getElementById(`rzp-tab-${t}`);
        const panel = document.getElementById(`rzp-panel-${t}`);
        if (tabBtn && panel) {
            if (t === tab) {
                tabBtn.className = "w-full text-left p-3 rounded-xl bg-white text-blue-600 shadow-sm flex items-center space-x-2 transition-all";
                panel.classList.remove('hidden');
            } else {
                tabBtn.className = "w-full text-left p-3 rounded-xl hover:bg-white/60 text-gray-600 flex items-center space-x-2 transition-all";
                panel.classList.add('hidden');
            }
        }
    });
}

function setUpiId(id) {
    const upiInput = document.getElementById('rzp-upi-input');
    if (upiInput) upiInput.value = id;
}

function openInteractiveRazorpayModal() {
    const flight = appState.flightToBook;
    if (!flight) return;

    const modal = document.getElementById('razorpay-interactive-modal');
    const amountEl = document.getElementById('rzp-modal-amount');
    const flightInfo = document.getElementById('rzp-modal-flight-info');
    const userInfo = document.getElementById('rzp-modal-user-info');
    const bodyEl = document.getElementById('rzp-modal-body');
    const procEl = document.getElementById('rzp-modal-processing');

    if (amountEl) amountEl.textContent = `₹${Number(flight.price).toLocaleString('en-IN')}`;
    if (flightInfo) flightInfo.textContent = `${flight.name} &bull; ${flight.flight_number || flight.flightNumber} (${flight.class})`;
    if (userInfo) userInfo.textContent = `${appState.userName} (${appState.userEmail || 'jaiswalbittu462@gmail.com'})`;

    if (bodyEl) bodyEl.classList.remove('hidden');
    if (procEl) procEl.classList.add('hidden');

    switchRzpTab('upi');
    openModal('razorpay-interactive-modal');
}

async function executeSimulatedRzpPayment(methodName) {
    const flight = appState.flightToBook;
    if (!flight) return;

    const bodyEl = document.getElementById('rzp-modal-body');
    const procEl = document.getElementById('rzp-modal-processing');
    const descEl = document.getElementById('rzp-processing-desc');

    if (bodyEl && procEl) {
        bodyEl.classList.add('hidden');
        procEl.classList.remove('hidden');
    }
    if (descEl) {
        descEl.textContent = `Authorizing ₹${Number(flight.price).toLocaleString('en-IN')} via ${methodName}...`;
    }

    const dateString = `${appState.selectedYear}-${String(appState.selectedMonth + 1).padStart(2, '0')}-${String(appState.selectedDate).padStart(2, '0')}`;
    const pnr = "BA" + Math.floor(1000 + Math.random() * 9000);
    const mockPaymentId = "pay_rzp_" + Math.floor(100000 + Math.random() * 900000);
    const mockOrderId = "order_rzp_" + Math.floor(100000 + Math.random() * 900000);

    try {
        // Step 1: Call real backend payment verification endpoint
        const verifyPayload = {
            razorpay_order_id: mockOrderId,
            razorpay_payment_id: mockPaymentId,
            razorpay_signature: "sandbox_verified_signature",
            booking_data: {
                pnr: pnr,
                user_name: appState.userName,
                flight_id: flight.flight_id || 1,
                flight_number: flight.flight_number || flight.flightNumber,
                airline: flight.name || flight.airline,
                origin: flight.from,
                destination: flight.to || appState.selectedLocation,
                travel_date: dateString,
                cabin_class: flight.class,
                adults: appState.selectedPeople.adults,
                children: appState.selectedPeople.children,
                seats: flight.seats,
                base_fare: flight.base_fare,
                dynamic_surcharge: flight.surcharge,
                total_price: flight.price
            }
        };

        const res = await fetch('/api/payment/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(verifyPayload)
        });

        const data = await res.json();
        
        setTimeout(() => {
            closeModal();
            if (data.success) {
                flight.pnr = data.booking.pnr;
                flight.gate = data.booking.gate;
                flight.payment_id = data.payment_id;
                flight.order_id = mockOrderId;
                appState.bookedFlight = flight;
                appState.flightToBook = null;

                showToast(`Payment of ₹${Number(flight.price).toLocaleString('en-IN')} Approved via Razorpay!`, "🎉");
                showPage('home');
                loadUserBookings();
            } else {
                showToast("Payment verification failed on server", "❌");
            }
        }, 1200);

    } catch (err) {
        console.error("Payment error:", err);
        closeModal();
        showToast("Error processing payment", "❌");
    }
}

// --- REAL WORKING RAZORPAY PAYMENT GATEWAY & CONFIGURATION ---
function openRzpKeyModal() {
    const input = document.getElementById('custom-rzp-key-id');
    const secretInput = document.getElementById('custom-rzp-key-secret');
    if (input) {
        input.value = appState.razorpayKeyId || "rzp_test_1DP5mmOlF5G5ag";
    }
    if (secretInput) {
        secretInput.value = "";
    }
    openModal('rzp-key-modal');
}

async function saveCustomRzpCredentials() {
    const keyInput = document.getElementById('custom-rzp-key-id');
    const secretInput = document.getElementById('custom-rzp-key-secret');
    const newKey = keyInput ? keyInput.value.trim() : "";
    const newSecret = secretInput ? secretInput.value.trim() : "";

    if (!newKey) {
        showToast("Please enter a valid Razorpay Key ID", "⚠️");
        return;
    }

    try {
        const res = await fetch('/api/payment/set-credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key_id: newKey, key_secret: newSecret })
        });
        const data = await res.json();
        if (data.success) {
            appState.razorpayKeyId = data.key_id;
            const badge = document.getElementById('current-rzp-key');
            if (badge) badge.textContent = data.key_id;
            closeModal();
            showToast("Razorpay credentials saved & activated!", "💳");
        } else {
            showToast("Failed to update credentials", "❌");
        }
    } catch (e) {
        console.error("Error setting razorpay credentials:", e);
        showToast("Error updating Razorpay credentials", "❌");
    }
}

async function resetDefaultRzpCredentials() {
    try {
        const res = await fetch('/api/payment/set-credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key_id: "rzp_test_1DP5mmOlF5G5ag", key_secret: "" })
        });
        const data = await res.json();
        appState.razorpayKeyId = "rzp_test_1DP5mmOlF5G5ag";
        const badge = document.getElementById('current-rzp-key');
        if (badge) badge.textContent = "rzp_test_1DP5mmOlF5G5ag";
        const input = document.getElementById('custom-rzp-key-id');
        if (input) input.value = "rzp_test_1DP5mmOlF5G5ag";
        closeModal();
        showToast("Reset to Razorpay Default Test Sandbox Key", "🔄");
    } catch (e) {
        console.error(e);
    }
}

async function launchRazorpayPayment() {
    const flight = appState.flightToBook;
    if (!flight) {
        showToast("No flight selected for payment", "⚠️");
        return;
    }

    const rzpBtn = document.getElementById('razorpay-pay-btn');
    const originalBtnText = rzpBtn ? rzpBtn.innerHTML : '';
    if (rzpBtn) {
        rzpBtn.disabled = true;
        rzpBtn.innerHTML = `<span>⏳ Connecting to Razorpay Gateway...</span>`;
    }

    // 1. Fetch public Razorpay key config
    let keyId = appState.razorpayKeyId || "rzp_test_1DP5mmOlF5G5ag";
    try {
        const cfgRes = await fetch('/api/payment/config');
        const cfgData = await cfgRes.json();
        if (cfgData.key_id) keyId = cfgData.key_id;
    } catch (e) {
        console.warn("Could not fetch rzp config", e);
    }

    const amountInPaise = Math.round(Number(flight.price) * 100);
    const dateString = `${appState.selectedYear}-${String(appState.selectedMonth + 1).padStart(2, '0')}-${String(appState.selectedDate).padStart(2, '0')}`;
    const pnr = "BA" + Math.floor(1000 + Math.random() * 9000);
    const seatString = flight.seats || (appState.selectedSeats && appState.selectedSeats.length > 0 ? appState.selectedSeats.join(', ') : '5B');
    const flightNum = flight.flight_number || flight.flightNumber || 'AI-101';
    const airlineName = flight.name || flight.airline || 'Air India';
    const originCity = flight.from || 'Mumbai';
    const destCity = flight.to || appState.selectedLocation || 'Dubai';

    // 2. Setup Official Razorpay Standard Checkout options
    const options = {
        key: keyId,
        amount: amountInPaise,
        currency: "INR",
        name: "Booking Adventures",
        description: `Flight Booking: ${airlineName} (${flightNum}) ${originCity} → ${destCity}`,
        image: "https://cdn-icons-png.flaticon.com/512/7893/7893979.png",
        prefill: {
            name: appState.userName || "Bittu Jaiswal",
            email: appState.userEmail || "jaiswalbittu462@gmail.com",
            contact: appState.userMobile || "7992414122"
        },
        notes: {
            pnr: pnr,
            flight_number: flightNum,
            seats: seatString,
            origin: originCity,
            destination: destCity
        },
        theme: {
            color: "#2563eb"
        },
        handler: async function (response) {
            console.log("Official Razorpay Checkout Success:", response);
            showToast("Payment captured by Razorpay! Verifying with backend...", "💳");

            try {
                const verifyPayload = {
                    razorpay_order_id: response.razorpay_order_id || ("ord_" + Math.random().toString(36).substring(2, 10)),
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature || "real_rzp_checkout_verified",
                    booking_data: {
                        pnr: pnr,
                        user_name: appState.userName,
                        flight_id: flight.flight_id || 1,
                        flight_number: flightNum,
                        airline: airlineName,
                        origin: originCity,
                        destination: destCity,
                        travel_date: dateString,
                        cabin_class: flight.class || 'Economy',
                        adults: appState.selectedPeople.adults || 1,
                        children: appState.selectedPeople.children || 0,
                        seats: seatString,
                        base_fare: flight.base_fare,
                        dynamic_surcharge: flight.surcharge,
                        total_price: flight.price
                    }
                };

                const res = await fetch('/api/payment/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(verifyPayload)
                });
                const data = await res.json();
                if (data.success) {
                    flight.pnr = data.booking.pnr;
                    flight.gate = data.booking.gate;
                    flight.payment_id = response.razorpay_payment_id;
                    flight.order_id = verifyPayload.razorpay_order_id;
                    flight.seats = seatString;
                    appState.bookedFlight = flight;
                    appState.flightToBook = null;

                    showToast(`Booking Confirmed! Razorpay Ref: ${response.razorpay_payment_id}`, "🎉");
                    showPage('home');
                    loadUserBookings();
                } else {
                    showToast("Payment verification failed on server.", "❌");
                }
            } catch (err) {
                console.error("Booking verification error:", err);
                flight.pnr = pnr;
                flight.gate = "G12";
                flight.payment_id = response.razorpay_payment_id;
                flight.seats = seatString;
                appState.bookedFlight = flight;
                appState.flightToBook = null;
                showToast("Booking recorded with Razorpay ID: " + response.razorpay_payment_id, "✅");
                showPage('home');
                loadUserBookings();
            } finally {
                if (rzpBtn) {
                    rzpBtn.disabled = false;
                    rzpBtn.innerHTML = originalBtnText || `<span>💳 Pay with Razorpay Gateway</span>`;
                }
            }
        },
        modal: {
            backdropclose: true,
            escape: true,
            handleback: true,
            confirm_close: true,
            ondismiss: function () {
                console.log("Razorpay Checkout Modal dismissed");
                showToast("Razorpay payment window closed.", "ℹ️");
                if (rzpBtn) {
                    rzpBtn.disabled = false;
                    rzpBtn.innerHTML = originalBtnText || `<span>💳 Pay with Razorpay Gateway</span>`;
                }
            }
        }
    };

    // 3. Launch official Razorpay standard checkout iframe
    try {
        if (typeof Razorpay === 'undefined') {
            throw new Error("Razorpay checkout SDK not loaded from CDN");
        }
        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (resp) {
            console.error("Razorpay Payment Failed:", resp.error);
            showToast(`Razorpay Payment Failed: ${resp.error.description || 'Transaction declined'}`, "❌");
            if (rzpBtn) {
                rzpBtn.disabled = false;
                rzpBtn.innerHTML = originalBtnText || `<span>💳 Pay with Razorpay Gateway</span>`;
            }
        });
        rzp.open();
        if (rzpBtn) {
            rzpBtn.disabled = false;
            rzpBtn.innerHTML = originalBtnText || `<span>💳 Pay with Razorpay Gateway</span>`;
        }
    } catch (e) {
        console.warn("Razorpay standard SDK launch note:", e);
        // Fallback to interactive modal only if network/popup blocker blocked Razorpay CDN
        openInteractiveRazorpayModal();
        if (rzpBtn) {
            rzpBtn.disabled = false;
            rzpBtn.innerHTML = originalBtnText || `<span>💳 Pay with Razorpay Gateway</span>`;
        }
    }
}

// Direct Sandbox One-Click Payment Simulation (Guaranteed to work even offline / without popup blocks)
async function processInstantSandboxPayment() {
    const flight = appState.flightToBook;
    if (!flight) return;

    const btn = document.getElementById('sandbox-pay-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="animate-pulse">Authorizing Sandbox Payment...</span>`;
    }

    const dateString = `${appState.selectedYear}-${String(appState.selectedMonth + 1).padStart(2, '0')}-${String(appState.selectedDate).padStart(2, '0')}`;
    const pnr = "BA" + Math.floor(1000 + Math.random() * 9000);
    const mockPaymentId = "pay_rzp_test_" + Math.floor(100000 + Math.random() * 900000);
    const mockOrderId = "order_rzp_" + Math.floor(100000 + Math.random() * 900000);

    try {
        const verifyPayload = {
            razorpay_order_id: mockOrderId,
            razorpay_payment_id: mockPaymentId,
            razorpay_signature: "sandbox_verified_signature",
            booking_data: {
                pnr: pnr,
                user_name: appState.userName,
                flight_id: flight.flight_id || 1,
                flight_number: flight.flight_number || flight.flightNumber,
                airline: flight.name || flight.airline,
                origin: flight.from,
                destination: flight.to || appState.selectedLocation,
                travel_date: dateString,
                cabin_class: flight.class,
                adults: appState.selectedPeople.adults,
                children: appState.selectedPeople.children,
                seats: flight.seats,
                base_fare: flight.base_fare,
                dynamic_surcharge: flight.surcharge,
                total_price: flight.price
            }
        };

        const res = await fetch('/api/payment/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(verifyPayload)
        });

        const data = await res.json();
        if (data.success) {
            flight.pnr = data.booking.pnr;
            flight.gate = data.booking.gate;
            flight.payment_id = data.payment_id;
            flight.order_id = mockOrderId;
            appState.bookedFlight = flight;
            appState.flightToBook = null;

            showToast(`Razorpay payment approved! ID: ${data.payment_id}`, "🎉");
            showPage('home');
            loadUserBookings();
        }
    } catch (err) {
        console.error(err);
        showToast("Error processing payment.", "❌");
    }
}

// --- USER BOOKINGS LIST & CANCELLATION ---
async function loadUserBookings() {
    const listContainer = document.getElementById('bookings-list');
    const badge = document.getElementById('nav-bookings-count');
    if (!listContainer) return;

    try {
        const res = await fetch(`/api/bookings/${encodeURIComponent(appState.userName)}`);
        const data = await res.json();
        const bookings = data.bookings || [];
        appState.userBookings = bookings;
        if (badge) badge.innerText = bookings.length;

        if (bookings.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center py-16">
                    <p class="text-5xl mb-4">🎫</p>
                    <h3 class="text-xl font-bold text-gray-800">No Bookings Yet</h3>
                    <p class="text-gray-500 text-sm mt-1">Book your first dynamically priced flight from the home screen.</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = '';
        bookings.forEach(b => {
            const isCancelled = b.payment_status === 'CANCELLED';
            const card = document.createElement('div');
            card.className = `p-6 rounded-2xl border transition-all ${
                isCancelled ? 'bg-gray-50 border-gray-200 opacity-60' : 'bg-white border-blue-100 shadow-sm hover:shadow-md'
            }`;

            card.innerHTML = `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="flex items-center space-x-3 mb-1">
                            <span class="text-xs font-mono font-bold bg-blue-100 text-blue-800 px-2.5 py-1 rounded">PNR: ${b.pnr}</span>
                            <span class="text-xs font-bold px-2 py-0.5 rounded-full ${isCancelled ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}">
                                ${b.payment_status}
                            </span>
                            <span class="text-xs font-semibold text-gray-500">${b.created_at}</span>
                        </div>
                        <h4 class="text-xl font-bold text-gray-800">${b.airline} &bull; ${b.flight_number}</h4>
                        <p class="text-sm text-gray-600">${b.origin} → ${b.destination} &bull; Date: <strong>${b.travel_date}</strong></p>
                        <p class="text-xs text-gray-500 mt-1">Seats: <strong>${b.seats}</strong> &bull; Class: <strong>${b.cabin_class}</strong> &bull; Gate: <strong>${b.gate}</strong></p>
                        ${b.payment_id ? `<p class="text-[11px] font-mono text-indigo-600 mt-0.5">💳 Razorpay Ref: <strong>${b.payment_id}</strong></p>` : ''}
                        ${b.refund_id ? `<p class="text-[11px] font-mono text-emerald-700 mt-0.5 font-bold">💸 Razorpay Refund: ${b.refund_id} (₹${b.refund_amount})</p>` : ''}
                    </div>

                    <div class="text-right flex flex-col md:items-end justify-between">
                        <p class="text-2xl font-black text-blue-700">₹${Number(b.total_price).toLocaleString('en-IN')}</p>
                        <div class="mt-3 flex space-x-2">
                            ${
                                !isCancelled
                                    ? `<button onclick="cancelBooking('${b.pnr}')" class="bg-red-50 hover:bg-red-100 text-red-600 text-xs font-bold py-2 px-3 rounded-lg transition-colors">
                                        Cancel & Refund
                                       </button>`
                                    : `<span class="text-xs text-gray-400 font-semibold py-2">Cancelled</span>`
                            }
                        </div>
                    </div>
                </div>
            `;
            listContainer.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load user bookings:", err);
    }
}

async function cancelBooking(pnr) {
    if (!confirm(`Are you sure you want to cancel booking ${pnr}? Dynamic refund policy applies.`)) return;

    try {
        const res = await fetch(`/api/bookings/cancel/${pnr}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`Booking cancelled. Refund of ₹${data.refund_amount} initiated!`, "💸");
            loadUserBookings();
            if (appState.bookedFlight && appState.bookedFlight.pnr === pnr) {
                appState.bookedFlight = null;
                renderHomePage();
            }
        }
    } catch (err) {
        showToast("Error processing cancellation.", "❌");
    }
}

// --- ML & PBL LAB METRICS & INTERACTIVE SIMULATOR ---
async function loadMLMetrics() {
    try {
        const res = await fetch('/api/ml/metrics');
        const data = await res.json();
        
        // Populate feature importance bars
        const fiContainer = document.getElementById('feature-importance-bars');
        if (fiContainer && data.feature_importance) {
            fiContainer.innerHTML = '';
            for (const [feat, val] of Object.entries(data.feature_importance)) {
                const pct = Math.round(val * 100);
                const featName = feat.replace(/_/g, ' ').toUpperCase();
                fiContainer.innerHTML += `
                    <div class="space-y-1">
                        <div class="flex justify-between text-xs font-semibold text-gray-700">
                            <span>${featName}</span>
                            <span>${pct}% (${val})</span>
                        </div>
                        <div class="progress-bar-container h-2 bg-gray-100">
                            <div class="progress-bar bg-blue-600" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }
        }
    } catch (err) {
        console.warn("Could not load ML metrics from API:", err);
    }
    runSimulator();
}

async function runSimulator() {
    const baseFare = parseFloat(document.getElementById('sim-base').value);
    const days = parseInt(document.getElementById('sim-days').value);
    const season = parseInt(document.getElementById('sim-season').value);
    const demand = parseInt(document.getElementById('sim-demand').value);
    const occ = parseInt(document.getElementById('sim-occ').value);
    const model = document.getElementById('sim-model').value;

    document.getElementById('sim-base-val').innerText = `₹${baseFare.toLocaleString('en-IN')}`;
    document.getElementById('sim-days-val').innerText = `${days} day${days > 1 ? 's' : ''}`;
    document.getElementById('sim-season-val').innerText = `${season}%`;
    document.getElementById('sim-demand-val').innerText = `${demand}%`;
    document.getElementById('sim-occ-val').innerText = `${occ}%`;

    try {
        const res = await fetch('/api/ml/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_fare: baseFare,
                days_to_departure: days,
                seasonality_percent: season,
                demand_percent: demand,
                competitor_percent: 50,
                occupancy_percent: occ,
                model_type: model
            })
        });

        const data = await res.json();
        const output = data.output;

        document.getElementById('sim-predicted-price').innerText = `₹${output.predicted_price.toLocaleString('en-IN')}`;
        document.getElementById('sim-surcharge').innerText = `+₹${output.surcharge.toLocaleString('en-IN')}`;
        document.getElementById('sim-multiplier').innerText = `${output.price_multiplier}x`;

        const recEl = document.getElementById('sim-rec');
        if (output.price_multiplier > 1.25) {
            recEl.innerText = "Surge Alert: Book Now";
            recEl.className = "text-xl font-bold text-red-400";
        } else if (output.price_multiplier > 1.05) {
            recEl.innerText = "Moderate Demand";
            recEl.className = "text-xl font-bold text-yellow-300";
        } else {
            recEl.innerText = "Fair / Off-Peak Price";
            recEl.className = "text-xl font-bold text-green-400";
        }
    } catch (err) {
        console.error(err);
    }
}

// --- PRICE FORECAST SVG CHART LOGIC ---
function renderPriceForecastChart() {
    const data = appState.priceForecast;
    const container = document.getElementById('price-forecast-chart');
    const recommendationEl = document.getElementById('ai-recommendation');
    const bookingTimeEl = document.getElementById('booking-time-recommendation');
    if (!container || !data || data.length === 0) return;

    const W = container.clientWidth || 240;
    const H = container.clientHeight || 96;

    const maxPrice = Math.max(...data);
    const minPrice = Math.min(...data);
    const priceRange = maxPrice - minPrice > 0 ? maxPrice - minPrice : 1;

    const points = data.map((price, i) => {
        const x = (i / (data.length - 1)) * (W - 20) + 10;
        const y = H - ((price - minPrice) / priceRange) * (H - 24) - 12;
        return `${x},${y}`;
    }).join(' ');

    const trend = data[data.length - 1] - data[0];
    let recommendationText = '';
    let trendColor = 'stroke-blue-500';

    if (trend > 1500) {
        recommendationText = 'Prices rising soon. <span class="text-red-600 font-bold">Book Now!</span>';
        trendColor = 'stroke-red-500';
        if (bookingTimeEl) bookingTimeEl.innerHTML = `AI suggests booking within <strong>3 hours</strong> before fare updates.`;
    } else if (trend < -1500) {
        recommendationText = 'Prices expected to drop. <span class="text-green-600 font-bold">Consider Waiting.</span>';
        trendColor = 'stroke-green-500';
        if (bookingTimeEl) bookingTimeEl.innerHTML = `AI predicts lower fares in <strong>2-3 days</strong>.`;
    } else {
        recommendationText = 'Prices are stable. Book at your convenience.';
        trendColor = 'stroke-blue-500';
        if (bookingTimeEl) bookingTimeEl.innerHTML = `Prices are stable across the next 7 days.`;
    }

    container.innerHTML = `
        <svg width="100%" height="100%" viewBox="0 0 ${W} ${H}" class="overflow-visible">
            <polyline class="chart-line ${trendColor}" points="${points}"/>
        </svg>
    `;
    if (recommendationEl) recommendationEl.innerHTML = recommendationText;
}

// --- INITIALIZE UI & DOM CONTENT ---
document.addEventListener('DOMContentLoaded', () => {
    // Populate About Page Content
    const aboutEl = document.getElementById('about');
    if (aboutEl) {
        aboutEl.innerHTML = `
            <div class="text-center max-w-3xl mx-auto">
                <span class="text-xs font-bold bg-blue-100 text-blue-800 px-3 py-1 rounded-full uppercase tracking-wider">Project-Based Learning (Sem 7)</span>
                <h2 class="text-4xl font-extrabold text-gray-900 mt-3 mb-3">The Machine Learning Intelligence Behind Your Journey</h2>
                <p class="text-base text-gray-600 leading-relaxed">
                    Designed to simulate enterprise-grade airline Revenue Management Systems (RMS), our engine balances airline profitability with passenger fairness using supervised Machine Learning.
                </p>
            </div>

            <div class="mt-12 grid md:grid-cols-3 gap-8 text-center">
                <div class="bg-gray-50 p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <div class="bg-blue-100 text-blue-600 rounded-2xl h-16 w-16 flex items-center justify-center mx-auto mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V8H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v4"/><path d="M4 12v8h14a2 2 0 0 0 2-2v-4a2 2 0 0 0-2-2h-3"/><path d="M12 12v8"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Multi-Source Ingestion</h3>
                    <p class="text-gray-500 text-sm mt-2">Continuously ingests historical booking logs, competitor price indices, real-time seat inventory, and seasonality flags.</p>
                </div>

                <div class="bg-gray-50 p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <div class="bg-purple-100 text-purple-600 rounded-2xl h-16 w-16 flex items-center justify-center mx-auto mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8V4H8"/><rect x="8" y="12" width="4" height="4"/><path d="M8 12H4v4"/><path d="m20 12-3-3 3-3"/><path d="m17 9 3 3-3 3"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Gradient Boosting ML Core</h3>
                    <p class="text-gray-500 text-sm mt-2">Leverages an ensemble of decision trees trained to minimize mean squared error across non-linear elasticity regimes.</p>
                </div>

                <div class="bg-gray-50 p-8 rounded-2xl border border-gray-100 shadow-sm">
                    <div class="bg-green-100 text-green-600 rounded-2xl h-16 w-16 flex items-center justify-center mx-auto mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/><path d="m12 12-2 2 2 2"/><path d="m19 12-2 2 2 2"/></svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-800">Sub-15ms REST API</h3>
                    <p class="text-gray-500 text-sm mt-2">Built on asynchronous FastAPI and SQLite for low-latency inferencing and atomic seat reservation safety.</p>
                </div>
            </div>
        `;
    }

    // Populate Destinations Page Content
    const destEl = document.getElementById('destinations');
    if (destEl) {
        destEl.innerHTML = `
            <div class="text-center mb-10">
                <span class="text-xs font-bold bg-blue-100 text-blue-800 px-3 py-1 rounded-full uppercase tracking-wider">Global Adventures</span>
                <h2 class="text-4xl font-extrabold text-gray-900 mt-2">Explore Top Destinations</h2>
                <p class="text-gray-500 text-sm mt-1">Get inspired for your next adventure with real-time ML flight rates.</p>
            </div>
            
            <div class="space-y-12">
                <!-- Russia -->
                <div class="grid md:grid-cols-2 gap-8 items-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <img src="https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?q=80&w=800&auto=format&fit=crop" class="rounded-2xl shadow-md w-full h-80 object-cover">
                    <div>
                        <span class="text-xs font-bold text-blue-600 uppercase">Eurasian Wonder</span>
                        <h3 class="text-3xl font-extrabold text-gray-900 mb-3">Russia</h3>
                        <p class="text-gray-600 text-sm mb-4">Experience the grandeur of Russia, from the historic heart of Moscow to the artistic soul of St. Petersburg.</p>
                        <h4 class="font-bold text-sm text-gray-800 mb-2">Top Experiences:</h4>
                        <ul class="list-disc list-inside text-xs text-gray-600 space-y-1">
                            <li>Ride the legendary Trans-Siberian Railway</li>
                            <li>Explore the Kremlin and Red Square in Moscow</li>
                            <li>Marvel at the art in the Hermitage Museum</li>
                        </ul>
                    </div>
                </div>

                <!-- Brazil -->
                <div class="grid md:grid-cols-2 gap-8 items-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <div class="md:order-2">
                        <img src="https://images.unsplash.com/photo-1483729558449-99ef09a8c325?q=80&w=800&auto=format&fit=crop" class="rounded-2xl shadow-md w-full h-80 object-cover">
                    </div>
                    <div class="md:order-1">
                        <span class="text-xs font-bold text-green-600 uppercase">South American Rhythms</span>
                        <h3 class="text-3xl font-extrabold text-gray-900 mb-3">Brazil</h3>
                        <p class="text-gray-600 text-sm mb-4">From the vibrant energy of Rio de Janeiro to the untouched wilderness of the Amazon, Brazil is unforgettable.</p>
                        <h4 class="font-bold text-sm text-gray-800 mb-2">Top Experiences:</h4>
                        <ul class="list-disc list-inside text-xs text-gray-600 space-y-1">
                            <li>Visit the Christ the Redeemer statue on Corcovado</li>
                            <li>Explore the Amazon Rainforest on an eco-cruise</li>
                            <li>Witness the thundering cascades of Iguazu Falls</li>
                        </ul>
                    </div>
                </div>

                <!-- Egypt -->
                <div class="grid md:grid-cols-2 gap-8 items-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <img src="https://images.unsplash.com/photo-1569949381669-ecf31ae8e613?q=80&w=800&auto=format&fit=crop" class="rounded-2xl shadow-md w-full h-80 object-cover">
                    <div>
                        <span class="text-xs font-bold text-amber-600 uppercase">Cradle of Civilization</span>
                        <h3 class="text-3xl font-extrabold text-gray-900 mb-3">Egypt</h3>
                        <p class="text-gray-600 text-sm mb-4">Journey back in time to the land of pharaohs. Explore ancient pyramids and sail down the majestic Nile River.</p>
                        <h4 class="font-bold text-sm text-gray-800 mb-2">Top Experiences:</h4>
                        <ul class="list-disc list-inside text-xs text-gray-600 space-y-1">
                            <li>Marvel at the Great Pyramids of Giza and Sphinx</li>
                            <li>Relax on a traditional felucca along the Nile</li>
                            <li>Explore the ancient temples of Luxor and Karnak</li>
                        </ul>
                    </div>
                </div>

                <!-- Italy -->
                <div class="grid md:grid-cols-2 gap-8 items-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <div class="md:order-2">
                        <img src="https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?q=80&w=800&auto=format&fit=crop" class="rounded-2xl shadow-md w-full h-80 object-cover">
                    </div>
                    <div class="md:order-1">
                        <span class="text-xs font-bold text-red-600 uppercase">Art & Gastronomy</span>
                        <h3 class="text-3xl font-extrabold text-gray-900 mb-3">Italy</h3>
                        <p class="text-gray-600 text-sm mb-4">A land where history, art, and world-class cuisine converge. From Roman ruins to Venice canals.</p>
                        <h4 class="font-bold text-sm text-gray-800 mb-2">Top Experiences:</h4>
                        <ul class="list-disc list-inside text-xs text-gray-600 space-y-1">
                            <li>Tour the Colosseum and Vatican City</li>
                            <li>Ride a gondola through the canals of Venice</li>
                            <li>Drive the cliffside turns of the Amalfi Coast</li>
                        </ul>
                    </div>
                </div>

                <!-- Japan -->
                <div class="grid md:grid-cols-2 gap-8 items-center bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                    <img src="https://images.unsplash.com/photo-1542051841857-5f90071e7989?q=80&w=800&auto=format&fit=crop" class="rounded-2xl shadow-md w-full h-80 object-cover">
                    <div>
                        <span class="text-xs font-bold text-indigo-600 uppercase">Tradition & Future</span>
                        <h3 class="text-3xl font-extrabold text-gray-900 mb-3">Japan</h3>
                        <p class="text-gray-600 text-sm mb-4">Discover a mesmerizing blend of serene ancient temples and futuristic technology in Tokyo, Kyoto, and Osaka.</p>
                        <h4 class="font-bold text-sm text-gray-800 mb-2">Top Experiences:</h4>
                        <ul class="list-disc list-inside text-xs text-gray-600 space-y-1">
                            <li>View snow-capped Mount Fuji from Lake Kawaguchiko</li>
                            <li>Cross the buzzing Shibuya intersection in Tokyo</li>
                            <li>Walk through the bamboo groves and shrines of Kyoto</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    // Populate Results Page Container Structure
    const resultsEl = document.getElementById('results');
    if (resultsEl) {
        resultsEl.innerHTML = `
            <div class="grid lg:grid-cols-4 gap-8">
                <!-- Flight Listings -->
                <div class="lg:col-span-3">
                    <div class="flex justify-between items-center mb-6">
                        <div>
                            <span class="text-xs font-bold text-blue-600 uppercase tracking-wider">AI Dynamic Pricing Active</span>
                            <h3 class="text-3xl font-black text-gray-900">Flights to <span id="destination-title" class="text-blue-600">...</span></h3>
                        </div>
                        <button onclick="showPage('home')" class="text-xs bg-white border border-gray-300 font-bold px-3 py-2 rounded-xl hover:bg-gray-50 transition-colors">
                            ← Change Search
                        </button>
                    </div>
                    <div id="flight-listings" class="space-y-4"></div>
                </div>

                <!-- AI Sidebar Telemetry -->
                <div class="lg:col-span-1 space-y-6">
                    <!-- Data Inputs -->
                    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h4 class="font-bold text-base mb-3 text-gray-800 flex items-center space-x-2">
                            <span>📡</span>
                            <span>Live Data Ingestion</span>
                        </h4>
                        <div class="space-y-2 text-xs text-gray-600 font-medium">
                            <div class="flex items-center"><svg class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>Historical Flight Records</div>
                            <div class="flex items-center"><svg class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>Competitor Aggregators</div>
                            <div class="flex items-center"><svg class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>Real-Time Capacity Ratio</div>
                            <div class="flex items-center"><svg class="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>Seasonal Urgency Multiplier</div>
                        </div>
                    </div>

                    <!-- Live Market Factors -->
                    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h4 class="font-bold text-base mb-4 text-gray-800 flex items-center space-x-2">
                            <span>⚡</span>
                            <span>Live Factor Weights</span>
                        </h4>
                        <div class="space-y-3 text-xs">
                            <div class="space-y-1">
                                <div class="flex justify-between font-semibold"><span>Seasonality</span><span id="seasonality-value">--%</span></div>
                                <div class="progress-bar-container h-2"><div id="seasonality-bar" class="progress-bar bg-green-500" style="width: 0%"></div></div>
                            </div>
                            <div class="space-y-1">
                                <div class="flex justify-between font-semibold"><span>Live Demand</span><span id="demand-value">--%</span></div>
                                <div class="progress-bar-container h-2"><div id="demand-bar" class="progress-bar bg-yellow-500" style="width: 0%"></div></div>
                            </div>
                            <div class="space-y-1">
                                <div class="flex justify-between font-semibold"><span>Competitor Index</span><span id="competition-value">--%</span></div>
                                <div class="progress-bar-container h-2"><div id="competition-bar" class="progress-bar bg-indigo-500" style="width: 0%"></div></div>
                            </div>
                        </div>
                    </div>

                    <!-- 7-Day Forecast -->
                    <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h4 class="font-bold text-base mb-2 text-gray-800">7-Day Price Forecast</h4>
                        <div id="price-forecast-chart" class="h-24 w-full my-2"></div>
                        <p id="ai-recommendation" class="text-xs text-center font-semibold mt-2 text-gray-700"></p>
                    </div>

                    <!-- Best Time To Book -->
                    <div class="bg-white p-6 rounded-2xl shadow-sm border border-blue-100 bg-blue-50/30">
                        <h4 class="font-bold text-base mb-2 text-blue-900">Best Time to Book</h4>
                        <p id="booking-time-recommendation" class="text-xs font-semibold text-blue-700">Analyzing price trends...</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Populate Payment Page Container Structure
    const paymentEl = document.getElementById('payment');
    if (paymentEl) {
        paymentEl.innerHTML = `
            <div class="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
                <!-- Summary -->
                <div class="bg-white p-8 rounded-3xl shadow-xl border border-gray-100 flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-6">
                            <h3 class="text-2xl font-black text-gray-800">Booking Summary</h3>
                            <span class="text-xs font-bold bg-blue-100 text-blue-700 px-3 py-1 rounded-full">Step 3 of 3</span>
                        </div>
                        <div id="payment-summary"></div>
                    </div>
                    <div class="border-t mt-6 pt-6">
                        <div class="flex justify-between font-black text-2xl text-blue-700">
                            <span>Total Due</span>
                            <span id="payment-total">₹0</span>
                        </div>
                        <p class="text-[11px] text-gray-400 mt-1">Includes all airport surcharges, dynamic demand index, and taxes.</p>
                    </div>
                </div>

                <!-- Razorpay Gateway Card -->
                <div class="bg-white p-8 rounded-3xl shadow-xl border border-blue-100 flex flex-col justify-between relative overflow-hidden">
                    <div class="absolute -top-12 -right-12 w-32 h-32 bg-blue-50 rounded-full filter blur-xl"></div>
                    
                    <div>
                        <div class="flex justify-between items-center mb-4">
                            <div class="flex items-center space-x-2">
                                <span class="text-xl">💳</span>
                                <h3 class="text-2xl font-black text-gray-900">Razorpay Gateway</h3>
                            </div>
                            <span class="text-[10px] font-bold bg-green-100 text-green-700 px-2.5 py-1 rounded-full uppercase tracking-wider">Sandbox Free Trial</span>
                        </div>
                        <p class="text-xs text-gray-500 mb-6 leading-relaxed">
                            Official Indian payment gateway. Supports <strong class="text-gray-700">UPI (GPay, PhonePe, Paytm, BHIM)</strong>, <strong class="text-gray-700">Cards</strong>, <strong class="text-gray-700">NetBanking</strong>, and <strong class="text-gray-700">Wallets</strong>.
                        </p>

                        <!-- Payment Methods Graphic Strip -->
                        <div class="bg-slate-50 p-4 rounded-2xl border border-slate-100 mb-6">
                            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-2">Accepted Payment Methods</span>
                            <div class="flex items-center space-x-3 text-xs font-bold text-gray-600">
                                <span class="bg-white px-2.5 py-1 rounded-lg border border-slate-200">UPI / QR</span>
                                <span class="bg-white px-2.5 py-1 rounded-lg border border-slate-200">Visa / MC / RuPay</span>
                                <span class="bg-white px-2.5 py-1 rounded-lg border border-slate-200">NetBanking</span>
                            </div>
                        </div>

                        <!-- Customer Details Info -->
                        <div class="text-xs text-gray-500 space-y-1 mb-4 bg-blue-50/50 p-3.5 rounded-xl border border-blue-100">
                            <div class="flex justify-between"><span>Passenger:</span> <strong id="pay-customer-name" class="text-gray-800">Bittu Jaiswal</strong></div>
                            <div class="flex justify-between"><span>Email:</span> <strong id="pay-customer-email" class="text-gray-800">jaiswalbittu462@gmail.com</strong></div>
                            <div class="flex justify-between"><span>Contact:</span> <strong id="pay-customer-phone" class="text-gray-800">+91 7992414122</strong></div>
                        </div>

                        <!-- Active Razorpay Key Badge & Settings -->
                        <div class="flex items-center justify-between text-[11px] bg-slate-100/90 px-3 py-2 rounded-xl mb-6 border border-slate-200">
                            <div class="flex items-center space-x-1.5 overflow-hidden">
                                <span class="text-gray-500 font-semibold">🔑 Key:</span>
                                <code id="current-rzp-key" class="font-mono text-blue-700 font-bold text-[10px] truncate max-w-[140px]">rzp_test_1DP5mmOlF5G5ag</code>
                            </div>
                            <button onclick="openRzpKeyModal()" class="text-blue-600 hover:text-blue-800 font-bold hover:underline ml-2 whitespace-nowrap text-[11px]">
                                ⚙️ Custom Key
                            </button>
                        </div>
                    </div>

                    <div class="space-y-3">
                        <!-- Primary: Official Razorpay Checkout Modal -->
                        <button id="razorpay-pay-btn" onclick="launchRazorpayPayment()" class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-black py-4 px-6 rounded-2xl transition-all shadow-lg shadow-blue-500/30 text-sm flex items-center justify-center space-x-2">
                            <span>💳 Pay with Razorpay Gateway</span>
                        </button>

                        <!-- Secondary: 1-Click Sandbox Test Bypass -->
                        <div class="pt-2 border-t border-slate-100 text-center">
                            <button id="sandbox-pay-btn" onclick="processInstantSandboxPayment()" class="text-xs font-bold text-gray-500 hover:text-blue-600 transition-colors py-1 flex items-center justify-center space-x-1 mx-auto">
                                <span>⚡ Instant Sandbox Pay (Skip Popup)</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Modal Button Listeners
    renderCountriesList();
    renderCalendar();

    document.getElementById('select-location-btn').addEventListener('click', () => {
        if (appState.selectedLocation) {
            document.getElementById('location-display').innerText = appState.selectedLocation;
            checkDiscoverButton();
            closeModal();
            showToast(`Selected destination: ${appState.selectedLocation}`);
        }
    });

    document.getElementById('select-date-btn').addEventListener('click', () => {
        if (appState.selectedDate) {
            document.getElementById('date-display').innerText = `${appState.selectedDate} ${getMonthName(appState.selectedMonth)} ${appState.selectedYear}`;
            checkDiscoverButton();
            closeModal();
            showToast(`Travel date set to ${appState.selectedDate} ${getMonthName(appState.selectedMonth)}`);
        }
    });

    document.getElementById('select-people-btn').addEventListener('click', closeModal);

    const searchTrigger = () => {
        if (appState.selectedLocation && appState.selectedDate) {
            runAiAnalysis();
        } else if (!appState.selectedLocation) {
            openModal('location-modal');
        } else {
            openModal('date-modal');
        }
    };

    const discBtn = document.getElementById('discover-now-btn');
    if (discBtn) discBtn.addEventListener('click', searchTrigger);

    const searchIconBtn = document.getElementById('search-icon-btn');
    if (searchIconBtn) searchIconBtn.addEventListener('click', searchTrigger);

    // Passenger Counters
    document.querySelectorAll('.counter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            const action = btn.dataset.action;
            let count = appState.selectedPeople[type];
            if (action === 'increment') count++;
            else if (count > (type === 'adults' ? 1 : 0)) count--;

            appState.selectedPeople[type] = count;
            document.getElementById(`${type}-count`).innerText = count;

            const total = appState.selectedPeople.adults + appState.selectedPeople.children;
            const display = document.getElementById('people-display');
            if (display) display.innerText = `${total} passenger${total > 1 ? 's' : ''} ➤`;
        });
    });

    // Default selection for immediate testing:
    appState.selectedLocation = "Italy";
    appState.selectedDate = 25;
    appState.selectedMonth = 10; // November
    appState.selectedYear = 2026;
    document.getElementById('location-display').innerText = "Italy";
    document.getElementById('date-display').innerText = "25 Nov 2026";
    checkDiscoverButton();

    updateHeaderUI();
    fetchLiveForexAndTelemetry();
    showPage('home');
    openModal('login-modal');
});

// ================= GEMINI 2.5 FLASH AI CUSTOMER SUPPORT CHAT =================
let supportChatHistory = [];
let isSupportOpen = false;

function toggleSupportChat() {
    const drawer = document.getElementById('support-chat-drawer');
    if (!drawer) return;
    isSupportOpen = !isSupportOpen;
    if (isSupportOpen) {
        drawer.classList.remove('hidden');
        const input = document.getElementById('support-input-text');
        if (input) setTimeout(() => input.focus(), 150);
    } else {
        drawer.classList.add('hidden');
    }
}

function sendQuickSupportPrompt(promptText) {
    const input = document.getElementById('support-input-text');
    if (input) input.value = promptText;
    handleSendSupportMessage();
}

function appendSupportMessage(sender, text) {
    const container = document.getElementById('support-messages');
    if (!container) return;

    const msgEl = document.createElement('div');
    msgEl.className = 'flex space-x-2' + (sender === 'user' ? ' justify-end' : '');

    let formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\*\s/g, '<br>&bull; ')
        .replace(/\n/g, '<br>');

    if (sender === 'user') {
        msgEl.innerHTML = `
            <div class="bg-blue-600 text-white p-3 rounded-2xl rounded-tr-none shadow-sm max-w-[85%] text-xs leading-relaxed">
                ${formattedText}
            </div>
            <div class="w-7 h-7 rounded-xl bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs flex-shrink-0">
                ${(appState.userName || 'B')[0]}
            </div>
        `;
    } else {
        msgEl.innerHTML = `
            <div class="w-7 h-7 rounded-xl bg-blue-100 flex items-center justify-center text-xs flex-shrink-0">🤖</div>
            <div class="bg-white border border-slate-200 text-gray-800 p-3 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] text-xs leading-relaxed">
                ${formattedText}
            </div>
        `;
    }

    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
}

async function handleSendSupportMessage() {
    const input = document.getElementById('support-input-text');
    const indicator = document.getElementById('support-typing-indicator');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;

    input.value = '';

    appendSupportMessage('user', text);
    supportChatHistory.push({ sender: 'user', text: text });

    if (indicator) indicator.classList.remove('hidden');

    try {
        const res = await fetch('/api/support/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                history: supportChatHistory,
                user_name: appState.userName || 'Bittu Jaiswal',
                user_email: appState.userEmail || 'jaiswalbittu462@gmail.com',
                user_mobile: appState.userMobile || '+91 7992414122'
            })
        });

        const data = await res.json();
        const reply = data.reply || "Thank you for asking! I'm here to assist you with flight details and bookings.";

        appendSupportMessage('assistant', reply);
        supportChatHistory.push({ sender: 'assistant', text: reply });

    } catch (err) {
        console.error("Support chat error:", err);
        appendSupportMessage('assistant', "I'm having slight trouble reaching Gemini right now. Please try again in a moment.");
    } finally {
        if (indicator) indicator.classList.add('hidden');
    }
}
