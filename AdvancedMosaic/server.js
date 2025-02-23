const express = require('express');
const { Groq } = require('groq-sdk');
const dotenv = require('dotenv');
dotenv.config();
const app = express();
const port = process.env.PORT || 3000;
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
app.use(express.static('public'));
app.get('/api/creative-prompt', async (req, res) => {
    const userPrompt = req.query.prompt || "Generate an advanced mosaic art prompt for creating a nature-inspired, 3D mosaic with intricate details and artistic effects.";
    try {
        const completion = await groq.chat.completions.create({
            model: "qwen-2.5-32b",
            messages: [{ role: "user", content: userPrompt }],
            temperature: 0.6,
            max_completion_tokens: 4096,
            top_p: 0.95,
            stream: false,
            stop: null
        });
        const result = completion.choices[0].message.content || "";
        res.json({ prompt: result });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
