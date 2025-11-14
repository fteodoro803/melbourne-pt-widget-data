# setup_env.py
from pathlib import Path


def generate_env():
    print("Local Development Environment Setup")
    print("-" * 35)

    # Define all environment variables needed
    env_vars = {
        'MONGO_PASSWORD': {
            'description': 'MongoDB password',
            'required': True,
        },
    }

    env_content = "# Generated .env file for local development\n"
    env_content += "# Never commit this file to Git\n"
    env_content += "# Created by setup_env.py\n\n"

    for var_name, config in env_vars.items():
        desc = config['description']
        default = config.get('default')
        required = config.get('required', False)

        if default:
            prompt = f"{desc} [{default}]: "
        else:
            prompt = f"{desc}: "

        value = input(prompt).strip()

        # Use default if empty and default exists
        if not value and default:
            value = default

        # Check if required
        if required and not value:
            print(f"❌ {var_name} is required!")
            return

        if value:
            env_content += f"{var_name}={value}\n"

    # Write to .env file
    env_file = Path('.env')

    if env_file.exists():
        response = input("\n⚠️  .env already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    env_file.write_text(env_content)
    print(f"\n✅ Created {env_file}")
    print("🔒 Remember: Never commit this file to Git!")


if __name__ == "__main__":
    generate_env()