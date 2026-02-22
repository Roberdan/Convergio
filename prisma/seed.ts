import 'dotenv/config';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error('DATABASE_URL is not configured.');
}

const adapter = new PrismaPg({ connectionString });
const prisma = new PrismaClient({ adapter });

async function main(): Promise<void> {
  await prisma.tier.upsert({
    where: { name: 'Trial' },
    update: { maxAgents: 10, maxConversations: 50 },
    create: {
      name: 'Trial',
      maxAgents: 10,
      maxConversations: 50,
    },
  });

  await prisma.tier.upsert({
    where: { name: 'Pro' },
    update: { maxAgents: null, maxConversations: null },
    create: {
      name: 'Pro',
      maxAgents: null,
      maxConversations: null,
    },
  });

  console.log('Seeded tiers: Trial and Pro');
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
