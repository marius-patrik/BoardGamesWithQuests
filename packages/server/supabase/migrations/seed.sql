-- Registry metadata must be generated from engine/operators.py without drift.
-- Binary assets are uploaded via server/asset service; metadata is relational.
-- Supabase Storage buckets are data rows and belong in DML, not in Prisma schema.
INSERT INTO storage.buckets(id,name,public, file_size_limit, allowed_mime_types)
VALUES ('bgwq-visuals','bgwq-visuals',false,2097152,ARRAY['image/png','image/webp'])
ON CONFLICT (id) DO NOTHING;

INSERT INTO bgwq.hooks (key,ordinal,summary) VALUES
 ('game.initialize',0,'Populate entity seeds and default values'),
 ('action.generate',10,'Produce candidate participant commands'),
 ('action.validate',20,'Validate candidate commands against configuration'),
 ('action.before',30,'Evaluate pre-transition automatic actions'),
 ('action.apply',40,'Execute validated command effects'),
 ('action.after',50,'Evaluate post-transition actions'),
 ('space.passed',55,'Notify configured traversal pass events'),
 ('space.landed',56,'Notify configured arrival'),
 ('phase.enter',60,'Enter configured phase'),
 ('phase.exit',65,'Exit configured phase'),
 ('card.drawn',68,'Resolve a drawn card through actions on its entity type'),
 ('decision.resolved',70,'Decision is ready for settlement'),
 ('objective.evaluate',80,'Evaluate configured objectives and quests'),
 ('game.evaluate',90,'Resolve configured terminal objectives')
ON CONFLICT (key) DO NOTHING;
