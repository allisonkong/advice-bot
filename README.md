## Setup instructions

1. Install [uv](https://docs.astral.sh/uv/)
2. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install-sdk)
3. Set up [gcloud credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc):
    * `gcloud init`
    * `gcloud auth application-default login`
4. Install the proto compiler (`sudo apt install protobuf-compiler`)
5. Build and run bot with `./run_dev.sh`
6. Run unit tests (there aren't many) with `py.test`

## Production notes

* `systemctl --user (start|status|stop|restart) advice_bot.service`
* `journalctl --user -u advice_bot.service`
* See https://wiki.archlinux.org/title/Systemd/User
