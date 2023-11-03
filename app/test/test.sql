CREATE TABLE ram_usage (
      time BIGINT UNSIGNED DEFAULT (UNIX_TIMESTAMP()*1000),
      ram FLOAT NOT NULL
    );
    CREATE TABLE cpu_usage (
      time BIGINT UNSIGNED DEFAULT (UNIX_TIMESTAMP()*1000),
      cpu FLOAT NOT NULL
    );

INSERT INTO ram_usage (ram) VALUES (50);
INSERT INTO ram_usage (time, ram) VALUES (UNIX_TIMESTAMP()*1000 + 1000, 60);
INSERT INTO ram_usage (time, ram) VALUES (UNIX_TIMESTAMP()*1000 + 2000, 70);

INSERT INTO cpu_usage (cpu) VALUES (10);
INSERT INTO cpu_usage (time, cpu) VALUES (UNIX_TIMESTAMP()*1000 + 1000, 20);
INSERT INTO cpu_usage (time, cpu) VALUES (UNIX_TIMESTAMP()*1000 + 2000, 30);