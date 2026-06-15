# Field Templates

Field templates are reusable `fields.json` starting points for common chemistry
and chemical engineering extraction tasks. They help users avoid building every
field list from scratch, but they are not official reporting standards and are
not production-validated schemas.

Templates contain field definitions only. They do not contain extracted research
results, copyrighted paper text, private PDFs, API keys, local paths, or
generated outputs from real papers. Every extracted table still needs human
verification against the original source.

## Choosing A Template

Choose the closest domain template, then delete fields that do not matter for
your review and add task-specific fields before running a large batch.

- Use `catalysis_reaction.json` for reaction-condition and performance tables.
- Use `materials_synthesis.json` for preparation routes and material properties.
- Use `environmental_treatment.json` for pollutant removal and treatment tests.
- Use `electrochemistry.json` for electrochemical cells, electrodes, and metrics.

Start with 3-5 PDFs and inspect the output before processing a larger corpus.
Templates are intentionally broad and should be narrowed for each review topic.

## Using Templates In The Web UI

1. Open the local Web UI.
2. In the field editing panel, choose a template from the field-template menu.
3. Confirm that the current fields can be replaced.
4. Review the loaded fields.
5. Remove irrelevant fields and add missing task-specific fields.
6. Run a small test batch.
7. Manually verify the Excel or CSV output against the source PDFs.

## Using Templates With CLI Or Config Files

The CLI accepts field configuration through the same project configuration flow
used by the app. A template JSON file can be copied into a local field config or
used as a starting point for a custom `fields` list.

Keep local config files such as `config.local.json` out of Git. Do not commit
private API keys, private PDF paths, generated real-paper outputs, logs, or
caches.

## Requirement Levels

Each field has a `requirement` value:

- `required`: core field for row quality. Missing required fields may cause a
  row to be treated as low quality.
- `recommended`: useful for review, but not always present in every paper.
- `optional`: context or caveat fields. Empty optional fields should not be
  treated as extraction failure by themselves.

Use required fields sparingly. A field should be required only when a useful row
is not meaningful without it.

## Template Details

### `catalysis_reaction.json`

- Domain: catalysis reactions and chemical reaction engineering.
- Suitable literature type: thermal catalysis, fixed-bed tests, batch reactions,
  gas-solid reactions, catalyst screening, reaction-condition tables, and
  product-distribution summaries.
- Key required fields: `source_file`, `study_system`, `feedstock`, `catalyst`,
  `reaction_temperature_c`, `conversion_percent`, `main_product`.
- Recommended fields: `reactor_type`, `reaction_pressure_mpa`,
  `space_velocity`, `selectivity_percent`, `yield_percent`,
  `data_source_location`.
- Optional fields: `reaction_name`, `co_feed`, `catalyst_composition`,
  `catalyst_preparation_method`, `reaction_time_h`, `byproducts`,
  `carbon_balance_percent`, `notes`.
- Common extraction mistakes: mixing conversion/selectivity/yield basis,
  confusing catalyst sample IDs with supports, losing units for pressure or
  space velocity, and extracting values from a different reaction condition row.
- Recommended PDF mode: `pymupdf4llm` for most papers; try `mineru` only for
  complex tables or scanned/table-heavy layouts; use `pypdf_text` as a stable
  fallback.
- Manual verification advice: check reaction-condition rows, product basis,
  unit conversions, and whether reported performance belongs to the same
  catalyst and feedstock.

### `materials_synthesis.json`

- Domain: materials synthesis and material-property extraction.
- Suitable literature type: oxides, carbon materials, adsorbents, membranes,
  zeolites, MOFs, composites, catalyst preparation, and heat-treatment studies.
- Key required fields: `material_name`, `material_category`, `precursor`,
  `synthesis_method`.
- Recommended fields: `source_file`, `synthesis_temperature_c`,
  `synthesis_time_h`, `calcination_temperature_c`, `atmosphere`,
  `surface_area_m2_g`.
- Optional fields: `solvent`, `calcination_time_h`, `ph`, `template_agent`,
  `drying_condition`, `pore_volume_cm3_g`, `particle_size_nm`,
  `crystal_phase`, `characterization_methods`, `target_application`, `notes`.
- Common extraction mistakes: merging multi-stage synthesis steps, confusing
  drying and calcination temperatures, missing atmosphere, and treating
  characterization values as synthesis conditions.
- Recommended PDF mode: `pymupdf4llm` for most synthesis descriptions; use
  `mineru` for dense synthesis tables or scanned methods pages; use
  `pypdf_text` for simple text-only PDFs.
- Manual verification advice: check multi-step procedures, precursor identity,
  temperature/time units, and whether material properties correspond to the same
  sample label.

### `environmental_treatment.json`

- Domain: environmental treatment and pollutant-removal workflows.
- Suitable literature type: adsorption, photocatalysis, oxidation/reduction,
  membrane separation, wastewater treatment, and remediation studies.
- Key required fields: `treatment_process`, `pollutant`,
  `initial_concentration_mg_l`, `catalyst_or_adsorbent`,
  `reaction_time_min`.
- Recommended fields: `source_file`, `dosage_g_l`, `ph`,
  `removal_efficiency_percent`, `degradation_efficiency_percent`,
  `adsorption_capacity_mg_g`, `data_source_location`.
- Optional fields: `solution_volume_ml`, `light_source`, `oxidant`,
  `temperature_c`, `rate_constant`, `water_matrix`, `analysis_method`,
  `reuse_cycles`, `notes`.
- Common extraction mistakes: treating removal and degradation as equivalent,
  losing concentration units, mixing adsorption capacity with removal
  efficiency, and ignoring matrix effects or pH basis.
- Recommended PDF mode: `pymupdf4llm` for normal text/table layouts; use
  `mineru` for image-heavy figures or complex treatment tables; use
  `pypdf_text` as a compatibility fallback.
- Manual verification advice: verify pollutant identity, initial concentration,
  time point, pH, material dosage, and whether efficiency values refer to
  removal, degradation, mineralization, or adsorption.

### `electrochemistry.json`

- Domain: electrochemistry, electrochemical energy, and electrocatalysis.
- Suitable literature type: batteries, supercapacitors, water splitting, oxygen
  reactions, carbon dioxide reduction, cyclic voltammetry, charge/discharge
  tests, and electrode-performance tables.
- Key required fields: `electrochemical_system`, `working_electrode`,
  `active_material`, `electrolyte`, `performance_metric`.
- Recommended fields: `source_file`, `reference_electrode`,
  `potential_window_v`, `current_density_ma_cm2`, `overpotential_mv`,
  `capacity_mah_g`, `specific_capacitance_f_g`, `data_source_location`.
- Optional fields: `counter_electrode`, `cell_configuration`,
  `loading_mg_cm2`, `tafel_slope_mv_dec`, `cycle_number`,
  `capacity_retention_percent`, `scan_rate_mv_s`, `test_temperature_c`,
  `notes`.
- Common extraction mistakes: mixing two-electrode and three-electrode data,
  losing reference-electrode scale, confusing geometric and mass-normalized
  current density, and extracting performance values without their test
  conditions.
- Recommended PDF mode: `pymupdf4llm` for most papers; use `mineru` for dense
  electrochemical tables or figure-caption-heavy PDFs; use `pypdf_text` for
  simple text extraction fallback.
- Manual verification advice: check reference scale, normalization basis,
  electrode loading, scan rate or current density, and whether performance
  values belong to the same cell configuration.

## Suggesting New Templates For Issue #11

Use issue #11 or the repository's field-template suggestion workflow to propose
new templates. Keep suggestions focused and safe:

- Use synthetic or public-safe examples only.
- Do not upload copyrighted papers.
- Do not upload private PDFs, unpublished manuscripts, confidential outputs, or
  private local paths.
- Do not include API keys, tokens, `config.local.json`, logs with secrets, or
  generated Excel/CSV outputs from real papers.
- Include the domain and literature type.
- Explain why the fields matter for a real review workflow.
- Mark each field as `required`, `recommended`, or `optional`.
- Include expected output shape or a small synthetic example when possible.
- Optional: include a draft `fields.json` using the same schema as the templates
  in this directory.

Suggested issue outline:

```markdown
Domain:
Suitable literature type:
Why these fields matter:
Key required fields:
Recommended fields:
Optional fields:
Common extraction mistakes:
Recommended PDF mode:
Synthetic/public-safe example:
Expected output shape:
Draft fields.json:
```

Field templates are early-stage review aids. They should be discussed, tested on
safe examples, and manually reviewed before being treated as useful defaults.
