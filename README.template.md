<!-- Generated from README.template.md by scripts/render_readme_cards.py. Edit the template (or config.json), not README.md. -->
<p>
  <img src="./cards/hero.svg" width="100%" alt="{{hero_alt}}" />
</p>

<p>
  <img src="./cards/graph.svg" width="100%" alt="Contribution graph for the last year" />
</p>

<p>
  <img src="./cards/months.svg" width="100%" alt="Contributions per month, with streaks and busiest day" />
</p>

<p>
  <a href="https://github.com/{{github_user}}?tab=repositories"><img src="./cards/build.svg" width="32.5%" alt="BUILD: contributions in the last year" /></a>
  <a href="{{leetcode_url}}"><img src="./cards/solve.svg" width="32.5%" alt="SOLVE: LeetCode rating" /></a>
  <a href="{{codeforces_url}}"><img src="./cards/compete.svg" width="32.5%" alt="COMPETE: Codeforces rating" /></a>
</p>

{{coding_block}}

<sub>Cards are drawn by <code>scripts/render_readme_cards.py</code> and refreshed every day by a GitHub Action.</sub>
