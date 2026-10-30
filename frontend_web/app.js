/**
 * MusicAI Pro - Apple Music Clean Application Logic & Sound Engine
 * Hybrid Recommendation System with authentic audio streaming,
 * dual-track radar comparison, interactive API testing, and playlist export.
 */

// ============================================================================
// CONFIGURATION & GLOBAL STATE
// ============================================================================
const API_BASE = window.location.origin.startsWith('file:') 
  ? 'http://127.0.0.1:8000' 
  : '';

const state = {
  basket: new Set(['Jerusalema', 'Kabza De Small', 'Water']),
  genreFilters: [],
  availableGenres: [],
  recommendations: [],
  popularTracks: [],
  currentTrackIndex: -1,
  currentTrack: null,
  isPlaying: false,
  isShuffle: false,
  repeatMode: 'all', // 'off' | 'all' | 'one'
  activeTab: 'listen-now',
  viewMode: 'grid', // 'grid' | 'table'
  radarChart: null,
  radarTrackA: null,
  radarTrackB: null,
  algoChart: null,
  searchTimeout: null,
  radarTimeout: null,
  previewCache: new Map(), // key -> { previewUrl, artworkUrl }
  artworkCache: new Map()  // spotify_id -> thumbnail_url
};

// Curated vinyl sleeve gradients
const VINYL_GRADIENTS = [
  'linear-gradient(135deg, #FF2D55 0%, #FF9500 100%)',
  'linear-gradient(135deg, #AF52DE 0%, #5856D6 100%)',
  'linear-gradient(135deg, #34C759 0%, #007AFF 100%)',
  'linear-gradient(135deg, #FF3B30 0%, #AF52DE 100%)',
  'linear-gradient(135deg, #FF9500 0%, #FF2D55 100%)',
  'linear-gradient(135deg, #007AFF 0%, #5856D6 100%)',
  'linear-gradient(135deg, #5856D6 0%, #FF2D55 100%)',
  'linear-gradient(135deg, #30B0C7 0%, #34C759 100%)'
];

function getGradient(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return VINYL_GRADIENTS[Math.abs(hash) % VINYL_GRADIENTS.length];
}

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initAudioEngine();
  renderHeroBasketChips();
  renderActiveGenreFilters();
  initKeyboardShortcuts();
  
  await loadAvailableGenres();
  await loadSystemStats();
  
  // Initial recommendations fetch
  fetchRecommendations();

  // Close search dropdown on click outside
  document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('search-dropdown');
    const input = document.getElementById('global-search');
    if (dropdown && !dropdown.contains(e.target) && e.target !== input) {
      dropdown.classList.add('hidden');
    }
  });

  if (window.lucide) lucide.createIcons();
});

// ============================================================================
// NATIVE HTML5 AUDIO ENGINE & SOUND MANAGEMENT
// ============================================================================
function initAudioEngine() {
  const audio = document.getElementById('audio-engine');
  if (!audio) return;

  audio.volume = 0.8;

  // Real-time Scrubber & Time Sync
  audio.addEventListener('timeupdate', () => {
    if (!audio.duration || isNaN(audio.duration)) return;
    const progress = (audio.currentTime / audio.duration) * 100;
    const fill = document.getElementById('player-scrubber-fill');
    if (fill) fill.style.width = `${progress}%`;

    const curTime = document.getElementById('player-cur-time');
    if (curTime) {
      const curSec = Math.floor(audio.currentTime);
      const formatted = `0:${curSec < 10 ? '0' : ''}${curSec}`;
      curTime.textContent = formatted;
    }

    const totalTime = document.getElementById('player-total-time');
    if (totalTime && audio.duration) {
      const durSec = Math.floor(audio.duration);
      totalTime.textContent = `0:${durSec < 10 ? '0' : ''}${durSec}`;
    }
  });

  audio.addEventListener('play', () => {
    state.isPlaying = true;
    updatePlayButton(true);
    updateActivePlayingCardHighlight();
    const eq = document.getElementById('player-eq');
    if (eq) eq.classList.remove('hidden');
  });

  audio.addEventListener('pause', () => {
    state.isPlaying = false;
    updatePlayButton(false);
    updateActivePlayingCardHighlight();
    const eq = document.getElementById('player-eq');
    if (eq) eq.classList.add('hidden');
  });

  audio.addEventListener('ended', () => {
    if (state.repeatMode === 'one') {
      audio.currentTime = 0;
      audio.play();
    } else {
      playNextTrack();
    }
  });

  audio.addEventListener('error', (e) => {
    console.warn('Audio stream error, engaging Web Audio synthesizer fallback:', e);
    if (state.currentTrack) {
      playSynthPreview(state.currentTrack.track_name);
    }
  });
}

function setVolume(val) {
  const audio = document.getElementById('audio-engine');
  const level = parseFloat(val);
  if (audio) {
    audio.volume = level;
    audio.muted = false;
  }
  const icon = document.getElementById('volume-icon');
  if (icon) {
    const iconName = level === 0 ? 'volume-x' : (level < 0.5 ? 'volume-1' : 'volume-2');
    icon.setAttribute('data-lucide', iconName);
    if (window.lucide) lucide.createIcons();
  }
}

function toggleMute() {
  const audio = document.getElementById('audio-engine');
  if (!audio) return;
  audio.muted = !audio.muted;
  const icon = document.getElementById('volume-icon');
  const slider = document.getElementById('volume-slider');

  if (audio.muted) {
    if (icon) icon.setAttribute('data-lucide', 'volume-x');
    if (slider) slider.value = 0;
  } else {
    if (icon) icon.setAttribute('data-lucide', 'volume-2');
    if (slider) slider.value = audio.volume;
  }
  if (window.lucide) lucide.createIcons();
}

function seekAudio(e) {
  const audio = document.getElementById('audio-engine');
  const track = e.currentTarget;
  const rect = track.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const fraction = Math.max(0, Math.min(1, clickX / rect.width));

  if (audio && audio.duration && !isNaN(audio.duration)) {
    audio.currentTime = fraction * audio.duration;
  }
}

function toggleShuffle() {
  state.isShuffle = !state.isShuffle;
  const btn = document.getElementById('player-shuffle-btn');
  if (btn) {
    btn.className = state.isShuffle 
      ? 'text-[#FA243C] font-bold transition-colors' 
      : 'text-neutral-400 hover:text-white transition-colors';
  }
  showToast(state.isShuffle ? 'Shuffle: ON' : 'Shuffle: OFF', 'shuffle');
}

function toggleRepeat() {
  const modes = ['off', 'all', 'one'];
  const curIdx = modes.indexOf(state.repeatMode);
  state.repeatMode = modes[(curIdx + 1) % modes.length];

  const btn = document.getElementById('player-repeat-btn');
  if (btn) {
    if (state.repeatMode === 'off') {
      btn.className = 'text-neutral-400 hover:text-white transition-colors';
      btn.innerHTML = `<i data-lucide="repeat" class="w-4 h-4"></i>`;
    } else if (state.repeatMode === 'all') {
      btn.className = 'text-[#FA243C] font-bold transition-colors';
      btn.innerHTML = `<i data-lucide="repeat" class="w-4 h-4"></i>`;
    } else {
      btn.className = 'text-[#FA243C] font-bold transition-colors';
      btn.innerHTML = `<i data-lucide="repeat-1" class="w-4 h-4"></i>`;
    }
    if (window.lucide) lucide.createIcons();
  }
  showToast(`Repeat: ${state.repeatMode.toUpperCase()}`, 'repeat');
}

// Web Audio API Synthesizer Fallback (sound is guaranteed)
let audioCtx = null;
function playSynthPreview(trackName) {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    if (!audioCtx) audioCtx = new AudioContext();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const chords = [
      [261.63, 329.63, 392.00], // C Maj
      [220.00, 261.63, 329.63], // A Min
      [174.61, 220.00, 261.63], // F Maj
      [196.00, 246.94, 293.66]  // G Maj
    ];
    const now = audioCtx.currentTime;
    chords.forEach((chord, step) => {
      chord.forEach(freq => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + step * 0.65);
        gain.gain.setValueAtTime(0.08, now + step * 0.65);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + step * 0.65 + 0.6);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + step * 0.65);
        osc.stop(now + step * 0.65 + 0.65);
      });
    });
  } catch (e) {
    console.warn('Synth error:', e);
  }
}

// ============================================================================
// AUDIO & ARTWORK RESOLVER (APPLE MUSIC / ITUNES AAC STREAMS)
// ============================================================================
function sanitizeSearchQuery(title, artist) {
  // Remove parenthesized features like "(feat. ...)" or "[Remix]" to maximize match rate
  const cleanTitle = (title || '').replace(/\s*[\(\[].*?[\)\]]/g, '').trim();
  const cleanArtist = (artist || '').split(/[,&]/)[0].trim();
  return `${cleanTitle} ${cleanArtist}`;
}

async function fetchPreviewAudioAndArtwork(trackName, artist) {
  const cacheKey = `${trackName}___${artist}`.toLowerCase();
  if (state.previewCache.has(cacheKey)) {
    return state.previewCache.get(cacheKey);
  }

  const queries = [
    sanitizeSearchQuery(trackName, artist),
    `${trackName} ${artist}`,
    trackName
  ];

  for (const q of queries) {
    try {
      const url = `https://itunes.apple.com/search?term=${encodeURIComponent(q)}&entity=song&limit=1`;
      const res = await fetch(url);
      if (!res.ok) continue;
      const data = await res.json();

      if (data.results && data.results.length > 0) {
        const match = data.results[0];
        const previewUrl = match.previewUrl;
        const artworkUrl = match.artworkUrl100 ? match.artworkUrl100.replace('100x100bb', '600x600bb') : null;

        const result = { previewUrl, artworkUrl };
        state.previewCache.set(cacheKey, result);
        return result;
      }
    } catch (err) {
      console.warn(`Search attempt error for "${q}":`, err);
    }
  }

  return null;
}

async function resolveArtwork(spotifyId, trackName, artist, imgElementId) {
  const cacheKey = `${trackName}___${artist}`.toLowerCase();
  if (state.previewCache.has(cacheKey) && state.previewCache.get(cacheKey).artworkUrl) {
    applyImageToElement(imgElementId, state.previewCache.get(cacheKey).artworkUrl);
    return;
  }

  if (spotifyId && state.artworkCache.has(spotifyId)) {
    applyImageToElement(imgElementId, state.artworkCache.get(spotifyId));
    return;
  }

  const previewData = await fetchPreviewAudioAndArtwork(trackName, artist);
  if (previewData && previewData.artworkUrl) {
    applyImageToElement(imgElementId, previewData.artworkUrl);
    return;
  }

  if (spotifyId) {
    try {
      const res = await fetch(`https://open.spotify.com/oembed?url=https://open.spotify.com/track/${spotifyId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.thumbnail_url) {
        state.artworkCache.set(spotifyId, data.thumbnail_url);
        applyImageToElement(imgElementId, data.thumbnail_url);
      }
    } catch (e) {
      // Graceful fallback to vinyl sleeve CSS gradient
    }
  }
}

function applyImageToElement(imgElementId, url) {
  const img = document.getElementById(imgElementId);
  if (img) {
    img.src = url;
    img.classList.remove('hidden');
  }
}

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const search = document.getElementById('global-search');
      if (search) search.focus();
    }
    // Space: Toggle playback (only when not typing in an input)
    if (e.code === 'Space' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault();
      toggleAudioPlayback();
    }
  });
}

// ============================================================================
// THEME MANAGEMENT (DARK / LIGHT)
// ============================================================================
function initTheme() {
  const saved = localStorage.getItem('musicai-theme') || 'dark';
  setTheme(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  setTheme(next);
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('musicai-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.setAttribute('data-lucide', theme === 'dark' ? 'sun' : 'moon');
    if (window.lucide) lucide.createIcons();
  }
  if (state.radarChart) updateRadarTheme();
}

// ============================================================================
// NAVIGATION TABS
// ============================================================================
function switchTab(tabId) {
  state.activeTab = tabId;
  const tabs = ['listen-now', 'charts', 'radar', 'system'];

  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    if (!el || !navBtn) return;

    if (t === tabId) {
      el.classList.remove('hidden');
      navBtn.className = 'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold text-[#FA243C] bg-neutral-200/60 dark:bg-neutral-800 transition-all';
    } else {
      el.classList.add('hidden');
      navBtn.className = 'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/50 transition-all';
    }
  });

  if (tabId === 'charts' && state.popularTracks.length === 0) {
    loadTopCharts('All');
  } else if (tabId === 'radar' && !state.radarChart) {
    initDefaultRadar();
  } else if (tabId === 'system') {
    loadSystemStats();
  }

  if (window.lucide) lucide.createIcons();
}

function setViewMode(mode) {
  state.viewMode = mode;
  const gridBtn = document.getElementById('view-grid-btn');
  const tableBtn = document.getElementById('view-table-btn');
  const grid = document.getElementById('recs-grid');
  const table = document.getElementById('recs-table');

  if (mode === 'grid') {
    gridBtn.className = 'p-1.5 rounded-lg text-white bg-[#FA243C] shadow-sm transition-all';
    tableBtn.className = 'p-1.5 rounded-lg text-neutral-400 hover:text-white transition-all';
    grid.classList.remove('hidden');
    table.classList.add('hidden');
  } else {
    tableBtn.className = 'p-1.5 rounded-lg text-white bg-[#FA243C] shadow-sm transition-all';
    gridBtn.className = 'p-1.5 rounded-lg text-neutral-400 hover:text-white transition-all';
    table.classList.remove('hidden');
    grid.classList.add('hidden');
  }

  renderRecommendations();
}

// ============================================================================
// TASTE PROFILE (BASKET) & GENRE FILTER MANAGEMENT
// ============================================================================
function renderHeroBasketChips() {
  const container = document.getElementById('hero-basket-chips');
  const badge = document.getElementById('sidebar-basket-badge');
  if (badge) badge.textContent = state.basket.size;

  if (state.basket.size === 0) {
    container.innerHTML = `<span class="text-xs text-neutral-400 italic">No seeds yet. Pick a preset or add below!</span>`;
    return;
  }

  container.innerHTML = Array.from(state.basket).map(item => `
    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/10 backdrop-blur-md shadow-sm transition-colors">
      <span class="max-w-[130px] truncate">${escapeHtml(item)}</span>
      <button onclick="removeFromBasket('${escapeHtml(item).replace(/'/g, "\\'")}')" class="text-neutral-400 hover:text-white transition-colors" title="Remove seed">
        <i data-lucide="x" class="w-3 h-3"></i>
      </button>
    </span>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

function addCustomSeed() {
  const input = document.getElementById('quick-add-seed-input');
  if (!input) return;
  const val = input.value.trim();
  if (val) {
    addToBasket(val);
    input.value = '';
    fetchRecommendations();
  }
}

function addToBasket(item) {
  if (!item) return;
  state.basket.add(item.trim());
  renderHeroBasketChips();
  showToast(`Added "${item}" to Taste Profile`, 'check-circle-2');
}

function removeFromBasket(item) {
  state.basket.delete(item);
  renderHeroBasketChips();
  showToast(`Removed "${item}" from Taste Profile`, 'trash-2');
  fetchRecommendations();
}

function addGenreFilter(genre) {
  if (!genre) return;
  if (!state.genreFilters.includes(genre)) {
    state.genreFilters.push(genre);
    renderActiveGenreFilters();
    fetchRecommendations();
    showToast(`Added filter: ${genre}`, 'filter');
  }
  document.getElementById('genre-filter-select').value = '';
}

function removeGenreFilter(genre) {
  state.genreFilters = state.genreFilters.filter(g => g !== genre);
  renderActiveGenreFilters();
  fetchRecommendations();
  showToast(`Removed filter: ${genre}`, 'filter');
}

function renderActiveGenreFilters() {
  const container = document.getElementById('active-genre-filters');
  if (!container) return;

  if (state.genreFilters.length === 0) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = state.genreFilters.map(g => `
    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#FA243C]/20 text-[#FA243C] border border-[#FA243C]/30">
      <span>${escapeHtml(g)}</span>
      <button onclick="removeGenreFilter('${escapeHtml(g).replace(/'/g, "\\'")}')" class="hover:text-white ml-0.5">
        <i data-lucide="x" class="w-3 h-3"></i>
      </button>
    </span>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

function toggleTasteBasketModal() {
  switchTab('listen-now');
  const el = document.getElementById('hero-basket-chips');
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

function applyPreset(vibe) {
  const presets = {
    amapiano: {
      basket: ['Kabza De Small', 'DJ Maphorisa', 'Young Stunna', 'Jerusalema'],
      genres: ['amapiano']
    },
    afrobeats: {
      basket: ['Burna Boy', 'Wizkid', 'Tems', 'Rema'],
      genres: ['afrobeats']
    },
    pop: {
      basket: ['Taylor Swift', 'Dua Lipa', 'The Weeknd', 'Ed Sheeran'],
      genres: ['pop']
    },
    rock: {
      basket: ['Coldplay', 'Imagine Dragons', 'Arctic Monkeys', 'Queen'],
      genres: ['rock']
    }
  };

  const preset = presets[vibe];
  if (!preset) return;

  state.basket = new Set(preset.basket);
  state.genreFilters = [...preset.genres];
  renderHeroBasketChips();
  renderActiveGenreFilters();
  showToast(`Applied preset: ${vibe.toUpperCase()}`, 'sparkles');
  fetchRecommendations();
}

// ============================================================================
// RECOMMENDATION ENGINE (LISTEN NOW)
// ============================================================================
async function fetchRecommendations() {
  const btn = document.getElementById('hero-refresh-btn');
  const grid = document.getElementById('recs-grid');
  const metaText = document.getElementById('recs-meta-text');
  const countBadge = document.getElementById('recs-count-badge');
  const slider = document.getElementById('diversity-slider');
  const sliderLabel = document.getElementById('diversity-label');

  const topK = slider ? parseInt(slider.value) : 12;
  if (sliderLabel) sliderLabel.textContent = topK;

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Blending...`;
  if (window.lucide) lucide.createIcons();

  grid.innerHTML = Array(topK).fill(0).map(() => `
    <div class="frosted-card rounded-2xl p-3 border border-neutral-200/80 dark:border-neutral-800 space-y-3">
      <div class="w-full aspect-square rounded-xl skeleton-shimmer"></div>
      <div class="h-4 rounded skeleton-shimmer w-3/4"></div>
      <div class="h-3 rounded skeleton-shimmer w-1/2"></div>
    </div>
  `).join('');

  const startTime = performance.now();

  try {
    const payload = {
      basket: Array.from(state.basket),
      genres: state.genreFilters.length > 0 ? state.genreFilters : null,
      top_k: topK
    };

    const res = await fetch(`${API_BASE}/api/v1/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const recs = await res.json();
    state.recommendations = recs;

    const duration = Math.round(performance.now() - startTime);
    countBadge.textContent = `${recs.length} tracks`;
    metaText.textContent = `Generated in ${duration}ms via Hybrid Association + Content Engine.`;
    document.getElementById('sidebar-latency-val').textContent = `${duration}ms`;

    const counts = { apriori: 0, content_based: 0, popular: 0 };
    recs.forEach(r => {
      if (counts[r.reason] !== undefined) counts[r.reason]++;
      else counts.popular++;
    });

    const summaryChips = document.getElementById('recs-summary-chips');
    summaryChips.innerHTML = `
      <span class="reason-pill reason-apriori">${counts.apriori} Apriori</span>
      <span class="reason-pill reason-content">${counts.content_based} Content</span>
      <span class="reason-pill reason-popular">${counts.popular} Popular</span>
    `;

    renderRecommendations();
    renderAlgorithmChart(counts);
    document.getElementById('recs-analytics').classList.remove('hidden');

  } catch (err) {
    console.error('Fetch recommendations error:', err);
    metaText.textContent = `Backend error: ${err.message}`;
    grid.innerHTML = `
      <div class="col-span-full py-12 text-center text-red-500 font-semibold text-xs">
        Failed to fetch recommendations from ${API_BASE || window.location.origin}.
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i> Refresh Hits`;
    if (window.lucide) lucide.createIcons();
  }
}

function renderRecommendations() {
  const grid = document.getElementById('recs-grid');
  const table = document.getElementById('recs-table');
  const recs = state.recommendations;

  if (recs.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full py-16 text-center frosted-card rounded-3xl p-8">
        <i data-lucide="music" class="w-12 h-12 mx-auto text-neutral-500 mb-3"></i>
        <h3 class="text-base font-bold text-neutral-800 dark:text-white">No tracks found</h3>
        <p class="text-xs text-neutral-400 mt-1">Try picking one of the 1-click vibe presets above!</p>
      </div>
    `;
    table.innerHTML = '';
    return;
  }

  // Render Grid View
  grid.innerHTML = recs.map((track, i) => {
    const gradient = getGradient(track.track_name + track.artist);
    const imgId = `rec-art-${i}`;
    const cardId = `rec-card-${i}`;
    const pillClass = track.reason === 'apriori' ? 'reason-apriori' : (track.reason === 'content_based' ? 'reason-content' : 'reason-popular');
    const reasonText = track.reason === 'apriori' ? 'Co-Listen' : (track.reason === 'content_based' ? 'Acoustic' : 'Trending');
    const safeTrack = JSON.stringify(track).replace(/"/g, '&quot;');

    // Check if this card is currently playing
    const isNowPlaying = state.currentTrack && state.currentTrack.track_name === track.track_name && state.isPlaying;

    setTimeout(() => resolveArtwork(track.spotify_id, track.track_name, track.artist, imgId), 15 * i);

    return `
      <div id="${cardId}" class="frosted-card rounded-2xl p-3 border border-neutral-200/80 dark:border-neutral-800 flex flex-col justify-between group ${isNowPlaying ? 'card-now-playing' : ''}">
        <div>
          <!-- Album Art Cover -->
          <div class="album-art-wrap mb-2.5 ${isNowPlaying ? 'is-playing' : ''}" style="background: ${gradient};">
            <img id="${imgId}" src="" alt="${escapeHtml(track.track_name)}" class="album-img hidden">
            
            <!-- Hover Play Button -->
            <div class="play-hover-overlay" onclick="handleCardPlayClick(${safeTrack}, ${i})">
              <div class="play-circle-btn">
                <i data-lucide="${isNowPlaying ? 'pause' : 'play'}" class="w-4 h-4 fill-current ml-0.5"></i>
              </div>
            </div>

            <!-- Reason Pill Floating on Art -->
            <span class="absolute top-2 left-2 ${pillClass} shadow-md backdrop-blur-md">
              ${reasonText}
            </span>

            <!-- Now Playing Animated Wave on Artwork -->
            ${isNowPlaying ? `
              <div class="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-md">
                <div class="eq-container"><span class="eq-bar"></span><span class="eq-bar"></span><span class="eq-bar"></span></div>
              </div>
            ` : ''}
          </div>

          <!-- Title & Artist -->
          <div class="space-y-0.5">
            <div class="flex items-center justify-between gap-1">
              <h4 class="text-xs font-bold text-neutral-900 dark:text-white truncate" title="${escapeHtml(track.track_name)}">
                ${escapeHtml(track.track_name)}
              </h4>
              <button onclick="addToBasket('${escapeHtml(track.artist).replace(/'/g, "\\'")}')" class="text-neutral-400 hover:text-[#FA243C] p-0.5" title="Add artist to taste basket">
                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
              </button>
            </div>
            <p class="text-[11px] text-neutral-500 dark:text-neutral-400 truncate font-medium">
              ${escapeHtml(track.artist)}
            </p>
          </div>
        </div>

        <!-- Footer Match Meter -->
        <div class="mt-2.5 pt-2 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[10px]">
          <span class="text-neutral-400 capitalize truncate max-w-[70px]">${escapeHtml(track.genre || 'South Africa')}</span>
          <span class="font-bold text-neutral-700 dark:text-neutral-300">${Math.round(track.score * 100)}% match</span>
        </div>
      </div>
    `;
  }).join('');

  // Render Table View
  table.innerHTML = `
    <table class="w-full text-left text-xs">
      <thead class="bg-neutral-100 dark:bg-neutral-800/60 text-neutral-400 border-b border-neutral-200 dark:border-neutral-800">
        <tr>
          <th class="py-3 px-4 w-12 font-bold uppercase">#</th>
          <th class="py-3 px-4 font-bold uppercase">Title</th>
          <th class="py-3 px-4 font-bold uppercase">Artist</th>
          <th class="py-3 px-4 font-bold uppercase">Genre</th>
          <th class="py-3 px-4 font-bold uppercase">Scoring Reason</th>
          <th class="py-3 px-4 font-bold uppercase text-right">Confidence</th>
          <th class="py-3 px-4 w-16 text-center font-bold uppercase">Play</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-neutral-100 dark:divide-neutral-800">
        ${recs.map((t, idx) => {
          const pillClass = t.reason === 'apriori' ? 'reason-apriori' : (t.reason === 'content_based' ? 'reason-content' : 'reason-popular');
          const safeTrack = JSON.stringify(t).replace(/"/g, '&quot;');
          const isNowPlaying = state.currentTrack && state.currentTrack.track_name === t.track_name && state.isPlaying;

          return `
            <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/40 transition-colors ${isNowPlaying ? 'bg-[#FA243C]/5 font-semibold' : ''}">
              <td class="py-3 px-4 font-bold text-neutral-400">${idx + 1}</td>
              <td class="py-3 px-4 font-bold text-neutral-900 dark:text-white truncate max-w-xs">
                ${escapeHtml(t.track_name)}
                ${isNowPlaying ? '<span class="ml-2 text-[#FA243C]">▶</span>' : ''}
              </td>
              <td class="py-3 px-4 text-neutral-500 dark:text-neutral-300 truncate max-w-xs">${escapeHtml(t.artist)}</td>
              <td class="py-3 px-4 capitalize text-neutral-400">${escapeHtml(t.genre || 'South Africa')}</td>
              <td class="py-3 px-4"><span class="${pillClass}">${escapeHtml(t.reason)}</span></td>
              <td class="py-3 px-4 text-right font-mono font-bold text-neutral-800 dark:text-neutral-200">${Math.round(t.score * 100)}%</td>
              <td class="py-3 px-4 text-center">
                <button onclick="handleCardPlayClick(${safeTrack}, ${idx})" class="p-1.5 rounded-full hover:bg-[#FA243C] hover:text-white text-neutral-400 transition-all">
                  <i data-lucide="${isNowPlaying ? 'pause' : 'play'}" class="w-3.5 h-3.5 fill-current"></i>
                </button>
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;

  if (window.lucide) lucide.createIcons();
}

function handleCardPlayClick(track, index) {
  if (state.currentTrack && state.currentTrack.track_name === track.track_name) {
    toggleAudioPlayback();
  } else {
    playTrack(track, index);
  }
}

function updateActivePlayingCardHighlight() {
  const recs = state.recommendations;
  recs.forEach((track, i) => {
    const card = document.getElementById(`rec-card-${i}`);
    if (!card) return;
    const isNowPlaying = state.currentTrack && state.currentTrack.track_name === track.track_name && state.isPlaying;
    if (isNowPlaying) {
      card.classList.add('card-now-playing');
    } else {
      card.classList.remove('card-now-playing');
    }
  });
}

// ============================================================================
// TOP CHARTS (TAB 2)
// ============================================================================
async function loadTopCharts(genre = 'All') {
  const grid = document.getElementById('charts-grid');
  grid.innerHTML = Array(12).fill(0).map(() => `
    <div class="frosted-card rounded-2xl p-3 border border-neutral-200/80 dark:border-neutral-800 space-y-3">
      <div class="w-full aspect-square rounded-xl skeleton-shimmer"></div>
      <div class="h-4 rounded skeleton-shimmer w-3/4"></div>
      <div class="h-3 rounded skeleton-shimmer w-1/2"></div>
    </div>
  `).join('');

  try {
    const url = genre && genre !== 'All' 
      ? `${API_BASE}/api/v1/popular?limit=18&genre=${encodeURIComponent(genre)}`
      : `${API_BASE}/api/v1/popular?limit=18`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const popularSongs = await res.json();
    state.popularTracks = popularSongs;

    grid.innerHTML = popularSongs.map((song, i) => {
      const gradient = getGradient(song.track_name + song.artist);
      const imgId = `chart-art-${i}`;
      const safeSong = JSON.stringify({
        track_name: song.track_name,
        artist: song.artist,
        spotify_id: song.spotify_id,
        genre: song.genre,
        score: song.popularity_score,
        reason: 'popular'
      }).replace(/"/g, '&quot;');

      setTimeout(() => resolveArtwork(song.spotify_id, song.track_name, song.artist, imgId), 15 * i);

      const rankBadgeColor = i === 0 ? 'bg-amber-400 text-black' : (i === 1 ? 'bg-slate-300 text-black' : (i === 2 ? 'bg-amber-700 text-white' : 'bg-black/50 text-white'));

      return `
        <div class="frosted-card rounded-2xl p-3 border border-neutral-200/80 dark:border-neutral-800 flex flex-col justify-between">
          <div>
            <div class="album-art-wrap mb-2.5" style="background: ${gradient};">
              <img id="${imgId}" src="" alt="${escapeHtml(song.track_name)}" class="album-img hidden">
              
              <span class="absolute top-2 left-2 px-2 py-0.5 rounded-md text-[10px] font-black uppercase shadow-md ${rankBadgeColor}">
                #${i + 1}
              </span>

              <div class="play-hover-overlay" onclick="playTrack(${safeSong}, ${i})">
                <div class="play-circle-btn">
                  <i data-lucide="play" class="w-4 h-4 fill-current ml-0.5"></i>
                </div>
              </div>
            </div>

            <h4 class="text-xs font-bold text-neutral-900 dark:text-white truncate" title="${escapeHtml(song.track_name)}">
              ${escapeHtml(song.track_name)}
            </h4>
            <p class="text-[11px] text-neutral-500 truncate mt-0.5">
              ${escapeHtml(song.artist)}
            </p>
          </div>

          <div class="mt-2.5 pt-2 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center justify-between text-[10px] text-neutral-400">
            <span class="capitalize truncate">${escapeHtml(song.genre || 'South Africa')}</span>
            <span class="font-bold text-neutral-700 dark:text-neutral-300">★ ${Math.round((song.popularity_score || 0.8) * 100)}</span>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    grid.innerHTML = `<div class="col-span-full py-8 text-center text-red-500 text-xs">Failed to load charts: ${err.message}</div>`;
  }
}

// ============================================================================
// ACOUSTIC RADAR & DUAL-TRACK COMPARISON (TAB 3)
// ============================================================================
function initDefaultRadar() {
  state.radarTrackA = {
    title: 'Jerusalema - Master KG',
    values: [0.85, 0.78, 0.90, 0.65, 0.95]
  };
  state.radarTrackB = null;
  renderDualRadarVisualizer();
}

function handleRadarSearch(val) {
  clearTimeout(state.radarTimeout);
  if (!val || val.trim().length < 2) {
    document.getElementById('radar-search-results').innerHTML = '';
    return;
  }

  state.radarTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/search?query=${encodeURIComponent(val)}&limit=6`);
      if (!res.ok) return;
      const songs = await res.json();
      
      const container = document.getElementById('radar-search-results');
      if (songs.length === 0) {
        container.innerHTML = `<p class="text-xs text-neutral-400 py-2">No matching songs found</p>`;
        return;
      }

      container.innerHTML = songs.map(s => {
        const safe = JSON.stringify(s).replace(/"/g, '&quot;');
        return `
          <div onclick="selectSongForRadar(${safe})" class="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer flex items-center justify-between transition-colors">
            <div class="truncate pr-2">
              <div class="text-xs font-bold text-neutral-800 dark:text-neutral-200 truncate">${escapeHtml(s.track_name)}</div>
              <div class="text-[10px] text-neutral-400 truncate">${escapeHtml(s.artist)}</div>
            </div>
            <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-neutral-400 flex-shrink-0"></i>
          </div>
        `;
      }).join('');
      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  }, 250);
}

function selectSongForRadar(song) {
  const title = `${song.track_name} - ${song.artist}`;
  const dance = song.danceability ?? 0.75;
  const energy = song.energy ?? 0.70;
  const valence = song.valence ?? 0.80;
  const tempoNorm = song.tempo ? Math.min(song.tempo / 180, 1.0) : 0.65;
  const pop = song.popularity_score ? Math.min(song.popularity_score / 100, 1.0) : 0.85;

  state.radarTrackA = {
    title,
    values: [dance, energy, valence, tempoNorm, pop]
  };

  renderDualRadarVisualizer();
  showToast(`Fingerprinted "${song.track_name}"`, 'radar');
}

function compareWithCurrentlyPlaying() {
  if (!state.currentTrack) {
    showToast('Play a song first to compare!', 'info');
    return;
  }

  const dance = state.currentTrack.danceability ?? 0.78;
  const energy = state.currentTrack.energy ?? 0.72;
  const valence = state.currentTrack.valence ?? 0.82;
  const tempoNorm = 0.70;
  const pop = state.currentTrack.score ? Math.min(state.currentTrack.score, 1.0) : 0.85;

  state.radarTrackB = {
    title: `${state.currentTrack.track_name} - ${state.currentTrack.artist}`,
    values: [dance, energy, valence, tempoNorm, pop]
  };

  renderDualRadarVisualizer();
  showToast(`Comparing with "${state.currentTrack.track_name}"`, 'git-compare');
}

function renderDualRadarVisualizer() {
  const canvas = document.getElementById('radar-canvas');
  if (!canvas || !state.radarTrackA) return;

  const isDark = (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)';
  const labelColor = isDark ? '#A1A1A6' : '#6E6E73';

  document.getElementById('radar-title').textContent = state.radarTrackA.title;
  const subtitle = document.getElementById('radar-subtitle');
  if (subtitle) {
    subtitle.textContent = state.radarTrackB 
      ? `Comparing Red: ${state.radarTrackA.title} vs Purple: ${state.radarTrackB.title}` 
      : 'Track 1 (Red)';
  }

  const datasets = [
    {
      label: state.radarTrackA.title,
      data: state.radarTrackA.values,
      backgroundColor: 'rgba(250, 36, 60, 0.28)',
      borderColor: '#FA243C',
      pointBackgroundColor: '#FA243C',
      pointBorderColor: '#fff',
      borderWidth: 2.5
    }
  ];

  if (state.radarTrackB) {
    datasets.push({
      label: state.radarTrackB.title,
      data: state.radarTrackB.values,
      backgroundColor: 'rgba(175, 82, 222, 0.25)',
      borderColor: '#AF52DE',
      pointBackgroundColor: '#AF52DE',
      pointBorderColor: '#fff',
      borderWidth: 2.5
    });
  }

  if (state.radarChart) state.radarChart.destroy();

  state.radarChart = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Danceability', 'Energy', 'Mood (Valence)', 'Tempo Pace', 'Popularity'],
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 1,
          ticks: { display: false },
          grid: { color: gridColor },
          angleLines: { color: gridColor },
          pointLabels: {
            color: labelColor,
            font: { size: 11, weight: '700' }
          }
        }
      },
      plugins: {
        legend: {
          display: !!state.radarTrackB,
          position: 'bottom',
          labels: { color: labelColor, font: { size: 10, weight: '600' } }
        }
      }
    }
  });
}

function updateRadarTheme() {
  if (!state.radarChart) return;
  const isDark = (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)';
  const labelColor = isDark ? '#A1A1A6' : '#6E6E73';
  state.radarChart.options.scales.r.grid.color = gridColor;
  state.radarChart.options.scales.r.angleLines.color = gridColor;
  state.radarChart.options.scales.r.pointLabels.color = labelColor;
  state.radarChart.update();
}

function renderAlgorithmChart(counts) {
  const canvas = document.getElementById('algorithm-chart');
  if (!canvas) return;

  if (state.algoChart) state.algoChart.destroy();

  state.algoChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Apriori Co-Listening', 'Content Audio Match', 'Regional Hits'],
      datasets: [{
        data: [counts.apriori, counts.content_based, counts.popular],
        backgroundColor: ['#34C759', '#AF52DE', '#FF9500'],
        borderWidth: 0,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '74%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 8,
            font: { size: 10, weight: '700' },
            color: '#86868B'
          }
        }
      }
    }
  });
}

// ============================================================================
// LIVE CATALOG SEARCH
// ============================================================================
function handleLiveSearch(query) {
  clearTimeout(state.searchTimeout);
  const dropdown = document.getElementById('search-dropdown');

  if (!query || query.trim().length < 2) {
    dropdown.classList.add('hidden');
    return;
  }

  state.searchTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/search?query=${encodeURIComponent(query)}&limit=6`);
      if (!res.ok) return;
      const results = await res.json();

      if (results.length === 0) {
        dropdown.innerHTML = `<div class="p-3 text-xs text-neutral-400 text-center">No songs found in catalog</div>`;
      } else {
        dropdown.innerHTML = results.map(s => {
          const safeTrack = JSON.stringify(s).replace(/"/g, '&quot;');
          return `
            <div class="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer flex items-center justify-between transition-colors">
              <div class="truncate pr-2" onclick="playTrack(${safeTrack})">
                <div class="text-xs font-bold text-neutral-900 dark:text-white truncate">${escapeHtml(s.track_name)}</div>
                <div class="text-[10px] text-neutral-500 dark:text-neutral-400 truncate">${escapeHtml(s.artist)}</div>
              </div>
              <div class="flex items-center gap-1.5 flex-shrink-0">
                <button onclick="playTrack(${safeTrack})" class="p-1 rounded-full text-neutral-400 hover:text-white hover:bg-[#FA243C]" title="Play Preview">
                  <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
                </button>
                <button onclick="addTrackFromSearch('${escapeHtml(s.track_name).replace(/'/g, "\\'")}', '${escapeHtml(s.artist).replace(/'/g, "\\'")}')" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FA243C]/10 text-[#FA243C] flex items-center gap-0.5 hover:bg-[#FA243C] hover:text-white transition-all">
                  <i data-lucide="plus" class="w-3 h-3"></i> Add
                </button>
              </div>
            </div>
          `;
        }).join('');
      }
      dropdown.classList.remove('hidden');
      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  }, 200);
}

function addTrackFromSearch(trackName, artist) {
  addToBasket(artist);
  document.getElementById('search-dropdown').classList.add('hidden');
  document.getElementById('global-search').value = '';
}

// ============================================================================
// PLAY TRACK & AUDIO STREAMING DISPATCHER
// ============================================================================
async function playTrack(track, index = -1) {
  state.currentTrack = track;
  state.currentTrackIndex = index;

  // Metadata Display
  document.getElementById('player-title').textContent = track.track_name;
  document.getElementById('player-artist').textContent = track.artist;

  // Reason Badge
  const reasonBadge = document.getElementById('player-reason-badge');
  if (track.reason) {
    reasonBadge.className = `hidden xl:inline-flex reason-pill ${track.reason === 'apriori' ? 'reason-apriori' : (track.reason === 'content_based' ? 'reason-content' : 'reason-popular')}`;
    reasonBadge.textContent = track.reason === 'apriori' ? 'Co-Listening' : (track.reason === 'content_based' ? 'Acoustic Match' : 'Regional Hit');
  }

  // Artwork resolution
  resolveArtwork(track.spotify_id, track.track_name, track.artist, 'player-art-img');

  // Spotify external link
  const spotifyLink = document.getElementById('player-spotify-link');
  if (track.spotify_id) {
    spotifyLink.href = `https://open.spotify.com/track/${track.spotify_id}`;
    spotifyLink.classList.remove('hidden');
  } else {
    spotifyLink.href = `https://open.spotify.com/search/${encodeURIComponent(track.track_name + ' ' + track.artist)}`;
    spotifyLink.classList.remove('hidden');
  }

  // Audio Playback
  const audio = document.getElementById('audio-engine');
  if (audio) {
    showToast(`Streaming audio for "${track.track_name}"`, 'volume-2');
    
    const previewData = await fetchPreviewAudioAndArtwork(track.track_name, track.artist);

    if (previewData && previewData.previewUrl) {
      audio.src = previewData.previewUrl;
      audio.play().then(() => {
        updateActivePlayingCardHighlight();
      }).catch(err => {
        console.warn('Autoplay prevented or network error:', err);
        showToast(`Click Play button to hear audio`, 'play');
      });
    } else {
      playSynthPreview(track.track_name);
      showToast(`Playing acoustic melody preview: "${track.track_name}"`, 'music');
    }
  }

  updatePlayButton(true);
}

function toggleAudioPlayback() {
  const audio = document.getElementById('audio-engine');
  if (!audio) return;

  if (audio.paused || audio.ended) {
    if (!audio.src && state.currentTrack) {
      playTrack(state.currentTrack, state.currentTrackIndex);
    } else {
      audio.play().then(() => {
        updatePlayButton(true);
        updateActivePlayingCardHighlight();
      }).catch(e => {
        console.warn('Playback error:', e);
      });
    }
  } else {
    audio.pause();
    updatePlayButton(false);
    updateActivePlayingCardHighlight();
  }
}

function updatePlayButton(isPlaying) {
  const icon = document.getElementById('player-play-icon');
  if (icon) {
    icon.setAttribute('data-lucide', isPlaying ? 'pause' : 'play');
    if (window.lucide) lucide.createIcons();
  }
}

function playNextTrack() {
  const list = state.recommendations.length > 0 ? state.recommendations : state.popularTracks;
  if (list.length === 0) return;

  let nextIdx;
  if (state.isShuffle) {
    nextIdx = Math.floor(Math.random() * list.length);
  } else {
    nextIdx = (state.currentTrackIndex + 1) % list.length;
  }
  playTrack(list[nextIdx], nextIdx);
}

function playPrevTrack() {
  const list = state.recommendations.length > 0 ? state.recommendations : state.popularTracks;
  if (list.length === 0) return;
  const prevIdx = (state.currentTrackIndex - 1 + list.length) % list.length;
  playTrack(list[prevIdx], prevIdx);
}

// ============================================================================
// EXPORT & SHARING
// ============================================================================
function openExportModal() {
  const modal = document.getElementById('export-modal');
  if (modal) modal.classList.add('active');
}

function closeExportModal() {
  const modal = document.getElementById('export-modal');
  if (modal) modal.classList.remove('active');
}

function copyTracklistToClipboard() {
  const recs = state.recommendations;
  if (recs.length === 0) {
    showToast('No tracks to export!', 'info');
    return;
  }

  const text = recs.map((t, i) => `${i + 1}. ${t.track_name} - ${t.artist} (${Math.round(t.score * 100)}% Match via ${t.reason})`).join('\n');
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied tracklist to clipboard!', 'check-circle-2');
    closeExportModal();
  });
}

function downloadM3UPlaylist() {
  const recs = state.recommendations;
  if (recs.length === 0) {
    showToast('No tracks to export!', 'info');
    return;
  }

  let m3u = '#EXTM3U\n';
  recs.forEach(t => {
    m3u += `#EXTINF:-1,${t.artist} - ${t.track_name}\n`;
    if (t.spotify_id) {
      m3u += `https://open.spotify.com/track/${t.spotify_id}\n`;
    } else {
      m3u += `# ${t.genre || 'South Africa'}\n`;
    }
  });

  const blob = new Blob([m3u], { type: 'audio/x-mpegurl' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `MusicAI_Recommendations_${Date.now()}.m3u`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast('Downloaded .M3U Playlist!', 'download');
  closeExportModal();
}

// ============================================================================
// INTERACTIVE API TESTER (TAB 4)
// ============================================================================
async function testApiRoute(path) {
  const output = document.getElementById('api-test-output');
  output.textContent = `Executing GET ${path}...`;
  const t0 = performance.now();

  try {
    const res = await fetch(`${API_BASE}${path}`);
    const data = await res.json();
    const duration = Math.round(performance.now() - t0);
    output.textContent = `// HTTP ${res.status} OK (${duration}ms)\n` + JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = `// Error executing ${path}:\n${err.message}`;
  }
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================
function showToast(message, iconName = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'apple-toast';
  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-4 h-4 text-[#FA243C]"></i>
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);

  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(12px)';
    toast.style.transition = 'all 0.2s ease';
    setTimeout(() => toast.remove(), 250);
  }, 2600);
}

// ============================================================================
// SYSTEM INFO & TELEMETRY
// ============================================================================
async function loadAvailableGenres() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/genres`);
    if (!res.ok) return;
    const data = await res.json();
    state.availableGenres = data.genres || [];

    const filterSelect = document.getElementById('genre-filter-select');
    const chartsSelect = document.getElementById('charts-genre-select');

    state.availableGenres.forEach(genre => {
      const opt = document.createElement('option');
      opt.value = genre;
      opt.textContent = genre.charAt(0).toUpperCase() + genre.slice(1);
      opt.className = 'bg-neutral-900 text-white';
      if (filterSelect) filterSelect.appendChild(opt);

      const opt2 = document.createElement('option');
      opt2.value = genre;
      opt2.textContent = genre.charAt(0).toUpperCase() + genre.slice(1);
      if (chartsSelect) chartsSelect.appendChild(opt2);
    });
  } catch (e) {
    console.error('Error loading genres:', e);
  }
}

async function loadSystemStats() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stats`);
    if (!res.ok) return;
    const stats = await res.json();

    const songs = document.getElementById('stat-songs');
    const rules = document.getElementById('stat-rules');
    const hist = document.getElementById('stat-history');
    const url = document.getElementById('stat-url');

    if (songs) songs.textContent = (stats.songs_count || 8681).toLocaleString();
    if (rules) rules.textContent = (stats.rules_count || 17150).toLocaleString();
    if (hist) hist.textContent = (stats.history_count || 1219845).toLocaleString();
    if (url) url.textContent = API_BASE || window.location.origin;
  } catch (e) {
    console.error('Error loading stats:', e);
  }
}

// ============================================================================
// UTILITIES
// ============================================================================
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
