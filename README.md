<a href="https://www.twilio.com">
  <img src="https://static0.twilio.com/marketing/bundles/marketing/img/logos/wordmark-red.svg" alt="Twilio" width="250" />
</a>

# Demo of our Agent Conference product and features

This demo of Twilio's Agent Conference product focuses on how its features can be used by management when monitoring and controlling their agent's calls.

Let's get started!

## Configure the sample application

To run the application, you'll need to gather your Twilio account credentials and configure them
in a file named `.env`. To create this file from an example template, do the following in your
Terminal.

```bash
cp .env.example .env
```

Open `.env` in your favorite text editor and configure the following values.

### Configure account information

Every sample in the demo requires some basic credentials from your Twilio account. Configure these first.

| Config Value  | Description |
| :-------------  |:------------- |
`TWILIO_ACCOUNT_SID` | Your primary Twilio account identifier - find this [in the console here](https://www.twilio.com/console).
`TWILIO_API_KEY` | Used to authenticate - [generate one here](https://www.twilio.com/console/dev-tools/api-keys).
`TWILIO_API_SECRET` | Used to authenticate - [just like the above, you'll get one here](https://www.twilio.com/console/dev-tools/api-keys).
`APPLICATION_SID` | Used for your Twilio Client outgoing calls - [generate your twiml app here](https://www.twilio.com/console/voice/twiml/apps).

#### A Note on API Keys

When you generate an API key pair at the URLs above, your API Secret will only be shown once -
make sure to save this information in a secure location, or possibly your `~/.bash_profile`.

#### Configuring Twilio Sync

Twilio Sync works out of the box, using default settings per account. Once you have your API keys configured, run the application (see below) and [open a browser](http://localhost:5000/)!

## Run the sample application

This application uses the lightweight [Flask Framework](http://flask.pocoo.org/).

We need to set up your Python environment. Install `virtualenv` via `pip`:

```bash
pip install virtualenv
```

Next, we need to install our dependencies:

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Now we should be all set! Run the application using the `python` command.

```bash
python app.py
```

Your application should now be running at [http://localhost:5000](http://localhost:5000). When you're finished, deactivate your virtual environment using `deactivate`.

![Alt text](static/img/ConferenceDemoHome.png?raw=true "Title")

## Running the demo with ngrok

```bash
ngrok http 5000
```
