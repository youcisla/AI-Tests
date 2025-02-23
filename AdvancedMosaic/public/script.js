document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('mosaicCanvas');
    const ctx = canvas.getContext('2d');
    const generateBtn = document.getElementById('generateBtn');
    const statusDiv = document.getElementById('status');
    const progressBar = document.getElementById('progressBar');
    const complexityInput = document.getElementById('complexity');
    const mosaicPromptInput = document.getElementById('mosaicPrompt');
    function getKeyword(text) {
        text = text.toLowerCase();
        if (text.includes("forest")) return "forest";
        if (text.includes("ocean")) return "ocean";
        if (text.includes("sunset")) return "sunset";
        if (text.includes("mountain")) return "mountain";
        return "nature";
    }
    function loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "Anonymous";
            img.onload = () => resolve(img);
            img.onerror = (e) => reject(e);
            img.src = url;
        });
    }
    function applyMosaic(image, tileSize) {
        const offCanvas = document.createElement('canvas');
        offCanvas.width = image.width;
        offCanvas.height = image.height;
        const offCtx = offCanvas.getContext('2d');
        offCtx.drawImage(image, 0, 0, image.width, image.height);
        const imgData = offCtx.getImageData(0, 0, image.width, image.height);
        const data = imgData.data;
        const width = image.width;
        const height = image.height;
        for (let y = 0; y < height; y += tileSize) {
            for (let x = 0; x < width; x += tileSize) {
                let r = 0, g = 0, b = 0, count = 0;
                for (let j = 0; j < tileSize; j++) {
                    for (let i = 0; i < tileSize; i++) {
                        const px = x + i;
                        const py = y + j;
                        if (px < width && py < height) {
                            const idx = (py * width + px) * 4;
                            r += data[idx];
                            g += data[idx + 1];
                            b += data[idx + 2];
                            count++;
                        }
                    }
                }
                r = Math.round(r / count);
                g = Math.round(g / count);
                b = Math.round(b / count);
                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x * (canvas.width / width), y * (canvas.height / height), tileSize * (canvas.width / width), tileSize * (canvas.height / height));
            }
            progressBar.style.width = `${(y / height) * 100}%`;
        }
    }
    async function fetchCreativePrompt(promptText) {
        const url = '/api/creative-prompt?prompt=' + encodeURIComponent(promptText);
        const res = await fetch(url);
        const data = await res.json();
        return data.prompt || "";
    }
    async function generateMosaic() {
        const complexity = parseInt(complexityInput.value);
        let creativeText = mosaicPromptInput.value.trim();
        if (creativeText) {
            statusDiv.textContent = 'Fetching creative prompt...';
            try {
                creativeText = await fetchCreativePrompt(creativeText);
            } catch (e) {
                creativeText = mosaicPromptInput.value.trim();
            }
        }
        const keyword = getKeyword(creativeText);
        const imageUrl = `https://source.unsplash.com/800x600/?${keyword}`;
        statusDiv.textContent = 'Loading image...';
        try {
            const img = await loadImage(imageUrl);
            statusDiv.textContent = 'Generating mosaic...';
            const tileSize = Math.max(5, 50 - complexity * 3);
            applyMosaic(img, tileSize);
            statusDiv.textContent = 'Mosaic generation complete.';
            progressBar.style.width = '100%';
        } catch (e) {
            statusDiv.textContent = 'Error loading image.';
        }
    }
    generateBtn.addEventListener('click', generateMosaic);
});
