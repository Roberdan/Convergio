-- AlterTable
ALTER TABLE "Invite" ADD COLUMN     "role" TEXT NOT NULL DEFAULT 'member',
ADD COLUMN     "status" TEXT NOT NULL DEFAULT 'pending',
ADD COLUMN     "type" TEXT NOT NULL DEFAULT 'human';

-- AlterTable
ALTER TABLE "Team" ADD COLUMN     "description" TEXT;

-- AlterTable
ALTER TABLE "TeamMember" ADD COLUMN     "agentId" UUID,
ADD COLUMN     "type" TEXT NOT NULL DEFAULT 'HUMAN',
ADD COLUMN     "userId" UUID,
ALTER COLUMN "role" SET DEFAULT 'member';
