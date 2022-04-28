# SI 507 Final Project

A simple map program gathers information of nearby electric vehicle chargers and shows their price and route information interactively.

Please create a `credentials.py` in the root of the project with the following code.

```python
NREL_API_KEY = 'see final report'
GMAP_API_KEY = 'see final report'
```

This application requires a running Redis database for caching, it can be set up by using docker with `docker-compose.yml` file provided in the repo.

For python, it requires Flask, redis, requests and Pillow, see requirements.txt for details.
