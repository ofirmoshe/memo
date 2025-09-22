const fs = require('fs');
const path = require('path');

// SVG template for app icon with black logo on white background
const createAppIconSVG = (size) => `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <!-- White background -->
  <rect width="${size}" height="${size}" fill="#FFFFFF" rx="${size * 0.18}" ry="${size * 0.18}"/>
  
  <!-- Black Memora logo centered -->
  <g transform="translate(${size * 0.2}, ${size * 0.2}) scale(${size * 0.6 / 1024})">
    <g transform="translate(0.000000,1024.000000) scale(0.100000,-0.100000)">
      <path d="M6796 7925 c-367 -60 -671 -244 -852 -517 -82 -122 -141 -248 -309
        -658 -359 -875 -440 -1070 -446 -1070 -4 0 -10 12 -14 28 -9 38 -499 1318
        -546 1426 -137 319 -377 557 -691 686 -354 146 -782 146 -1122 1 -446 -191
        -733 -551 -800 -1003 -14 -92 -16 -280 -16 -1429 0 -841 4 -1364 10 -1434 47
        -487 289 -818 695 -948 206 -66 532 -63 717 7 354 133 577 415 664 841 21 101
        31 491 24 920 -5 310 -5 310 -31 366 -34 72 -96 134 -168 168 -49 23 -68 26
        -161 26 -86 0 -114 -4 -151 -22 -63 -29 -125 -87 -157 -147 l-27 -51 -6 -580
        c-6 -622 -6 -621 -60 -730 -29 -57 -95 -120 -157 -148 -67 -31 -227 -31 -293
        -1 -86 40 -146 119 -186 249 -17 57 -18 128 -18 1420 0 1530 -5 1430 76 1594
        60 122 154 214 280 274 124 60 180 72 324 72 142 -1 212 -16 335 -77 67 -32
        102 -59 165 -122 92 -93 138 -172 208 -362 57 -151 223 -582 432 -1119 90
        -231 248 -636 350 -900 279 -722 324 -829 398 -960 269 -471 665 -755 1189
        -851 121 -22 367 -29 496 -14 618 72 1117 470 1301 1040 69 214 66 140 66
        1620 0 1227 -2 1343 -18 1430 -91 493 -446 846 -970 961 -123 27 -404 35 -531
        14z m386 -669 c110 -24 210 -76 282 -148 67 -68 105 -135 133 -238 17 -61 18
        -150 18 -1355 l0 -1290 -23 -83 c-45 -164 -117 -287 -230 -394 -160 -151 -364
        -229 -602 -229 -184 0 -297 25 -455 101 -157 76 -281 191 -374 348 -24 39 -98
        219 -175 422 -73 195 -145 385 -159 421 l-25 66 28 64 c15 35 114 264 220 509
        106 245 288 668 406 941 117 273 230 525 250 560 56 96 173 208 264 252 41 20
        100 43 130 51 71 19 227 20 312 2z" 
        fill="#000000" stroke="none"/>
    </g>
  </g>
</svg>`;

// Create splash screen SVG (larger logo for loading screen)
const createSplashIconSVG = (size) => `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <!-- White background -->
  <rect width="${size}" height="${size}" fill="#FFFFFF"/>
  
  <!-- Black Memora logo centered (larger for splash) -->
  <g transform="translate(${size * 0.15}, ${size * 0.15}) scale(${size * 0.7 / 1024})">
    <g transform="translate(0.000000,1024.000000) scale(0.100000,-0.100000)">
      <path d="M6796 7925 c-367 -60 -671 -244 -852 -517 -82 -122 -141 -248 -309
        -658 -359 -875 -440 -1070 -446 -1070 -4 0 -10 12 -14 28 -9 38 -499 1318
        -546 1426 -137 319 -377 557 -691 686 -354 146 -782 146 -1122 1 -446 -191
        -733 -551 -800 -1003 -14 -92 -16 -280 -16 -1429 0 -841 4 -1364 10 -1434 47
        -487 289 -818 695 -948 206 -66 532 -63 717 7 354 133 577 415 664 841 21 101
        31 491 24 920 -5 310 -5 310 -31 366 -34 72 -96 134 -168 168 -49 23 -68 26
        -161 26 -86 0 -114 -4 -151 -22 -63 -29 -125 -87 -157 -147 l-27 -51 -6 -580
        c-6 -622 -6 -621 -60 -730 -29 -57 -95 -120 -157 -148 -67 -31 -227 -31 -293
        -1 -86 40 -146 119 -186 249 -17 57 -18 128 -18 1420 0 1530 -5 1430 76 1594
        60 122 154 214 280 274 124 60 180 72 324 72 142 -1 212 -16 335 -77 67 -32
        102 -59 165 -122 92 -93 138 -172 208 -362 57 -151 223 -582 432 -1119 90
        -231 248 -636 350 -900 279 -722 324 -829 398 -960 269 -471 665 -755 1189
        -851 121 -22 367 -29 496 -14 618 72 1117 470 1301 1040 69 214 66 140 66
        1620 0 1227 -2 1343 -18 1430 -91 493 -446 846 -970 961 -123 27 -404 35 -531
        14z m386 -669 c110 -24 210 -76 282 -148 67 -68 105 -135 133 -238 17 -61 18
        -150 18 -1355 l0 -1290 -23 -83 c-45 -164 -117 -287 -230 -394 -160 -151 -364
        -229 -602 -229 -184 0 -297 25 -455 101 -157 76 -281 191 -374 348 -24 39 -98
        219 -175 422 -73 195 -145 385 -159 421 l-25 66 28 64 c15 35 114 264 220 509
        106 245 288 668 406 941 117 273 230 525 250 560 56 96 173 208 264 252 41 20
        100 43 130 51 71 19 227 20 312 2z" 
        fill="#000000" stroke="none"/>
    </g>
  </g>
</svg>`;

// Generate all required icon sizes
const generateIcons = () => {
  const assetsDir = path.join(__dirname, 'assets');
  
  // App icon (1024x1024 for iOS, will be scaled down automatically)
  const iconSVG = createAppIconSVG(1024);
  fs.writeFileSync(path.join(assetsDir, 'icon.svg'), iconSVG);
  console.log('✅ Generated icon.svg');
  
  // Adaptive icon for Android (512x512)
  const adaptiveIconSVG = createAppIconSVG(512);
  fs.writeFileSync(path.join(assetsDir, 'adaptive-icon.svg'), adaptiveIconSVG);
  console.log('✅ Generated adaptive-icon.svg');
  
  // Splash screen icon (512x512)
  const splashIconSVG = createSplashIconSVG(512);
  fs.writeFileSync(path.join(assetsDir, 'splash-icon.svg'), splashIconSVG);
  console.log('✅ Generated splash-icon.svg');
  
  // Favicon (256x256)
  const faviconSVG = createAppIconSVG(256);
  fs.writeFileSync(path.join(assetsDir, 'favicon.svg'), faviconSVG);
  console.log('✅ Generated favicon.svg');
  
  console.log('\n🎨 Icon generation complete!');
  console.log('📝 Next steps:');
  console.log('1. Convert SVG files to PNG using an online converter or imagemagick');
  console.log('2. Replace the existing PNG files with the new ones');
  console.log('3. The icons feature a black Memora logo on white background');
  console.log('\n💡 For automatic conversion, install imagemagick and run:');
  console.log('   magick convert icon.svg icon.png');
  console.log('   magick convert adaptive-icon.svg adaptive-icon.png');
  console.log('   magick convert splash-icon.svg splash-icon.png');
  console.log('   magick convert favicon.svg favicon.png');
};

generateIcons(); 