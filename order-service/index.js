const express = require('express');
const mongoose = require('mongoose');
const amqp = require('amqplib');

const app = express();
app.use(express.json());

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/orders';
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';
const QUEUE_NAME = 'order_queue';

// MongoDB Setup
mongoose.connect(MONGO_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

const Order = mongoose.model('Order', {
  customerName: String,
  item: String,
  amount: Number,
  status: { type: String, default: 'PENDING' }
});

// RabbitMQ Setup
let channel;
async function connectRabbitMQ() {
  try {
    const connection = await amqp.connect(RABBITMQ_URL);
    channel = await connection.createChannel();
    await channel.assertQueue(QUEUE_NAME, { durable: true });
    console.log('Connected to RabbitMQ');
  } catch (error) {
    console.error('RabbitMQ connection error, retrying in 5s...', error);
    setTimeout(connectRabbitMQ, 5000); // Retry logic penting buat microservices
  }
}
connectRabbitMQ();

// API Endpoint
app.post('/api/orders', async (req, res) => {
  const { customerName, item, amount } = req.body;

  try {
    // 1. Simpan ke MongoDB
    const order = new Order({ customerName, item, amount });
    const savedOrder = await order.save();
    console.log(`Order saved in DB: ${savedOrder._id}`);

    // 2. Kirim ke RabbitMQ
    if (channel) {
      const payload = {
        orderId: savedOrder._id,
        amount: savedOrder.amount,
        customerName: savedOrder.customerName
      };
      channel.sendToQueue(QUEUE_NAME, Buffer.from(JSON.stringify(payload)), { persistent: true });
      console.log(`Order sent to queue: ${savedOrder._id}`);
    }

    res.status(201).json(savedOrder);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/orders', async (req, res) => {
    const orders = await Order.find();
    res.json(orders);
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Order Service running on port ${PORT}`));
