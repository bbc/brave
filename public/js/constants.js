const POLL_FREQUENCY = 5000

const PATTERN_TYPES = [
    'SMPTE 100% color bars',
    'Random (television snow)',
    '100% Black',
    '100% White',
    'Red',
    'Green',
    'Blue',
    'Checkers 1px',
    'Checkers 2px',
    'Checkers 4px',
    'Checkers 8px',
    'Circular',
    'Blink',
    'SMPTE 75% color bars',
    'Zone plate',
    'Gamut checkers',
    'Chroma zone plate',
    'Solid color',
    'Moving ball',
    'SMPTE 100% color bars',
    'Bar',
    'Pinwheel',
    'Spokes',
    'Gradient',
    'Colors'
]

const WAVE_TYPES = [
    'Sine',
    'Square',
    'Saw',
    'Triangle',
    'Silence',
    'White uniform noise',
    'Pink noise',
    'Sine table',
    'Periodic Ticks',
    'White Gaussian noise',
    'Red (brownian) noise',
    'Blue noise',
    'Violet noise'
]

// Widescreen, selectively taken from https://en.wikipedia.org/wiki/16:9#Common_resolutions
var STANDARD_DIMENSIONS = [
    [254, 144],
    [480, 270],
    [640, 360],
    [768, 432],
    [1024, 576],
    [1280, 720],
    [1366, 768],

    // // Portrait
    // [360, 640],
    // [720, 1280],
    //
    // // Square
    // [360, 360],
    // [640, 640],
    // [1080, 1080],
    //
    // // 4:3
    // [640, 480],
    // [704, 576],
]
