# xiaomi_miio_waterpurifier_yunmi

Home Assistant custom component for Xiaomi Water Purifier C1, based on `python-miio` package

## Currently supported model

* [yunmi.waterpuri.lx9](https://home.miot-spec.com/spec/yunmi.waterpuri.lx9)
* [yunmi.waterpuri.lx11](https://home.miot-spec.com/spec/yunmi.waterpuri.lx11)

## Example Configuration

```yaml
sensor:
    - platform: xiaomi_miio_waterpurifier_yunmi
      name: 'Xiaomi Water Purifier C1'
      host: <host_ip>
      token: <host_token>
```

## Entities provided

* Error reason
* Filter#1 (PPC) remaining time (h)
* Filter#1 (PPC) used time (h)
* Filter#1 (PPC) remaining flow (L)
* Filter#1 (PPC) used flow (L)
* Filter#2 (RO) remaining time (h)
* Filter#2 (RO) used time (h)
* Filter#2 (RO) remaining flow (L)
* Filter#2 (RO) used flow (L)
* Filter#3 (CB) remaining time (h)
* Filter#3 (CB) used time (h)
* Filter#3 (CB) remaining flow (L)
* Filter#3 (CB) used flow (L)
* In water TDS (ppm)
* Out water TDS (ppm)
* Rinsing
* Water temperature (°C)