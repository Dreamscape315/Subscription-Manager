# Subscription Manager

## Description

This subscription management system allows you to organize original subscriptions while
leveraging the Subconverter backend and its built-in rule sets to merge multiple sources
into new, optimized subscription links with permanent URLs. Simplify your subscription management
workflow by transforming scattered proxy resources into coherent, customized configurations with
just a few clicks.

## Features

- **Subscription Management**: Easily manage and organize your subscriptions.
- **Subscription Conversion**: Convert your subscriptions by subconverter backend.
- **Generate Permanent URLs**: Create permanent URLs for your subscriptions.



## Requirements

- **Python 3.12**: Ensure you have Python 3.12 or higher installed on your system.

## Usage

### Cloning the Repository

1. **Clone the Repository**: Clone this repository to your local machine using Git.
```
git clone https://github.com/Dreamscape315/Subscription-Manager.git
```
2. **Install Dependencies**: Navigate to the project directory and install the required dependencies using pip.

```
cd Subscription-Manager
```

```
pip install -r requirements.txt
```
3. **Run the Application**: After installing the dependencies, you can run the application using the following command:
```
python run.py
```

### Docker

```
docker pull dreamscape315419/subscription-manager
```
```
docker run -d --name subscription-manager -p 5000:5000 dreamscape315419/subscription-manager
```

## Note

1. **The target of subconverter in this project is default as 'clash', other targets are not supported yet.**
2. **When your base URL is not HTTPS, you are unable to use copy link button.**

