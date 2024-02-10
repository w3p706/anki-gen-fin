To apply a migration in Tortoise ORM, especially after making changes to your models (like adding `null=True` to make a field nullable), you need to follow a specific set of steps. Tortoise ORM supports automatic migration generation and application through its `aerich` migration tool. Here's how you can set up and use `aerich` for migrations with Tortoise ORM:

### Step 1: Install Aerich

First, ensure you have `aerich` installed. If not, you can install it using pip:

```bash
pip install aerich
```

### Step 2: Initialize Aerich for Your Project

You need to initialize `aerich` with your Tortoise ORM models. This step generates an `aerich.ini` configuration file and a migrations folder in your project directory.

- Ensure your Tortoise ORM config is correctly set up in your project.
- Run the following command in the terminal at the root of your project:

```bash
aerich init -t db.TORTOISE_ORM
```

Replace `db.TORTOISE_ORM` with the actual import path to your Tortoise ORM config dictionary.

### Step 3: Initialize Aerich for Your Database

After initializing `aerich`, you need to initialize it for your specific database to prepare it for managing migrations:

```bash
aerich init-db
```

This command creates the initial migration and prepares the database for tracking migrations managed by `aerich`.

### Step 4: Create Migrations After Model Changes

Whenever you make changes to your models (like making a field nullable), you need to create a migration file that represents these changes:

```bash
aerich migrate --name some_migration_name
```

Replace `some_migration_name` with a meaningful name for your migration. `aerich` will generate a new migration file in the migrations directory.

### Step 5: Apply Migrations

To apply the generated migration(s) to your database, use the following command:

```bash
aerich upgrade
```

This command applies all unapplied migrations to your database, altering the schema as needed according to the changes defined in the migrations.

### Note:

- **Rollback:** If you need to rollback the last applied migration, you can use `aerich downgrade`.
- **Configuration:** Ensure `aerich.ini` and your Tortoise ORM configuration correctly reflect your database and app settings.
- **Version Control:** It's good practice to include migration files in your version control system to keep track of schema changes across different environments and team members.

Following these steps will help you manage your database schema changes smoothly with Tortoise ORM and `aerich`.