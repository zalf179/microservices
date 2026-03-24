const express = require('express');
const mongoose = require('mongoose');
const amqp = require('amqplib');
const path = require('path');

const app = express();
app.use(express.json()); // PENTING: Biar bisa baca JSON dari frontend
app.use(express.static(path.join(__dirname, 'public')));

const MONGO_URI = process.env.MONGO_URI || 'mongodb://mongodb:27017/orders';
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://rabbitmq:5672';
const QUEUE_NAME = 'order_queue';

// --- KONEKSI ---
mongoose.connect(MONGO_URI)
    .then(() => console.log('✅ Connected to MongoDB'))
    .catch(e => console.error('❌ MongoDB Error', e));

const Order = mongoose.model('Order', {
    customerName: String,
    item: String,
    amount: Number,
    status: { type: String, default: 'PENDING' }
});

let channel;
async function connectRabbitMQ() {
    try {
        const connection = await amqp.connect(RABBITMQ_URL);
        channel = await connection.createChannel();
        await channel.assertQueue(QUEUE_NAME, { durable: true });
        console.log('✅ Connected to RabbitMQ - Channel Ready');
    } catch (e) {
        console.log('❌ RabbitMQ Re-connecting...');
        setTimeout(connectRabbitMQ, 5000);
    }
}
connectRabbitMQ();

// --- ROUTES ---

app.post('/api/orders', async (req, res) => {
    // DEBUG: Liat data yang masuk di terminal
    console.log("� Request masuk ke /api/orders:", req.body);

    const { customerName, item, amount } = req.body;

    // VALIDASI (Penyebab Error 400)
    if (!customerName || !item || !amount) {
        console.log("⚠️ Validasi gagal! Ada field yang kosong.");
        return res.status(400).json({ error: "Data gak lengkap, bos!" });
    }

    try {
        const newOrder = new Order({ customerName, item, amount });
        const savedOrder = await newOrder.save();

        if (channel) {
            const msg = { orderId: savedOrder._id, amount, customerName };
            channel.sendToQueue(QUEUE_NAME, Buffer.from(JSON.stringify(msg)), { persistent: true });
            console.log("� Berhasil kirim pesan ke RabbitMQ");
        }

        res.status(201).json(savedOrder);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/orders', async (req, res) => {
    const orders = await Order.find().sort({ _id: -1 });
    res.json(orders);
});

app.listen(3000, () => console.log('� Order Service on port 3000'));