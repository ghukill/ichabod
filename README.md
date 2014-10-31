ichabod
=======

<h2>Description</h2>
The headless, page rendering, detective of website congruence.  Add websites to monitor to a simple config.json file, calibrate ichabod to a known working version of the site, then use ichabod to monitor the fully-rendered HTML of the page against the calibrated version.  Uses the Fuzzy Wuzzy library for fuzzy HTML matching; matching below configured congruency triggers emails and alerts.  

<h2>Requires</h2>
<ul>
  <li>The really neat, "<a href="https://github.com/scrapinghub/splash">Splash - Javascript rendering service</a>"</li>
  <li><a href="https://github.com/seatgeek/fuzzywuzzy">Fuzzy Wuzzy</a></li>
</ul>

<h2>Installation</h2>
<ol>
  <li>Clone repository</li>
  <li>Copy config_template.json to config.json, add sites and adjust settings</li>
  <li>Calibrate websites: <em>python main.py calibrate</em></li>
  <li>Check websites: <em>python main.py check (runs checks associated with each page, per config.json)</em></li>
  <li>Optional: add as cron job, hourly, 30 minutes, etc.</li>
<ol>
