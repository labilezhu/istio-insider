

### Ref

> https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html

```md

{ref}`图：Istio数据面架构`

```

#### Cross-referencing using roles
> https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html#cross-referencing-using-roles

```{note}
本节的实验环境说明见于： {ref}`appendix-lab-env/appendix-lab-env-base:简单分层实验环境`
```


#### Automatically label sections[¶](https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html#automatically-label-sections)

Manually adding an explicit target to each section and making sure is unique is a big task! Fortunately, Sphinx includes an extension to help us with that problem, [autosectionlabel](https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html).

To activate the `autosectionlabel` extension, add this to your `conf.py` file:

```
# Add the extension
extensions = [
   'sphinx.ext.autosectionlabel',
]

# Make sure the target is unique
autosectionlabel_prefix_document = True
```

Sphinx will create explicit targets for all your sections, the name of target has the form `{path/to/page}:{title-of-section}`.


List all ref taget
```bash
python -m sphinx.ext.intersphinx ./docs/build/html/objects.inv
```