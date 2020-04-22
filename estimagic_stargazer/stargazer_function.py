"""
A python package (function) to generate tables with regression results in html
and latex formats.
The package is based on the work by Matthew Burke (github.com/mwburke), that in
in its turn is based on R package of the same name:
https://CRAN.R-project.org/package=stargazer.

The package improves on Burke's work by being more flexible in terms of regression
results that can be passed, making it possible to produce tables for models beyond
statsmodels linear regression.

"""

import numpy as np
from numpy import round, sqrt, nan, isnan, digitize
import pandas as pd
from collections import namedtuple


# write functions to exctract params dataframe from statsmodels results
def extract_params_from_sm(model):
    to_concat = []
    params_list = ["params", "pvalues", "bse"]
    for col in params_list:
        to_concat.append(getattr(model, col))
    to_concat.append(model.conf_int()[0])
    to_concat.append(model.conf_int()[1])
    params_df = pd.concat(to_concat, axis=1)
    params_df.columns = ["value", "pvalue", "standard_error", "ci_lower", "ci_upper"]
    return params_df


def extract_info_from_sm(model):
    info = {}
    key_values = [
        "rsquared",
        "rsquared_adj",
        "scale",
        "fvalue",
        "f_pvalue",
        "df_model",
        "df_resid",
    ]
    for kv in key_values:
        info[kv] = getattr(model, kv)
    info["dependent_variable"] = model.model.endog_names
    return info


def Stargazer_table(models,table_dict,table_type):
    """Read arguments from table_dict and create html or Tex table summarizing
    results of models.

    Args:
        models: regression result (or list of results) in dictionary, statsmodels
            namedtuple format.
        table_dict (dict): dictionary of arguments analogous to Stargazer
            attributes.
        table_type (str): an argument determining the type of table to produce.
            "html" is for html table, "latex" is for Tex table.
    """
    table_specs = {}
    if isinstance(models, list):
        tables_specs
    pass
class Stargazer:
    """
    Class that is constructed with one or more trained
    OLS models from the statsmodels package.

    The user then can change the rendering options by
    chaining different methods to the Stargazer object
    and then render the results in either HTML or LaTeX.
    """

    def __init__(self, models):
        if isinstance(models, list):
            self.models = models
        else:
            self.models = [models]
        self.num_models = len(self.models)
        self.reset_params()
        self.extract_data()

    def validate_input(self):
        """
        Check inputs to see if they are going to
        cause any problems further down the line.

        Any future checking will be added here.
        """
        for i, mod in enumerate(self.models):
            if hasattr(mod, "params") and hasattr(mod, "info"):
                assert isinstance(mod.info, dict)
                assert isinstance(mod.params, pd.DataFrame)
            elif isinstance(mod, dict):
                NamedTup = namedtuple("NamedTup", "params info")
                self.models[i] = NamedTup(params=mod["params"], info=mod["info"])
            else:
                try:
                    NamedTup = namedtuple("NamedTup", "params info")
                    self.models[i] = NamedTup(
                        params=extract_params_from_sm(mod),
                        info={**extract_info_from_sm(mod)},
                    )
                # assume its a statsmodels results object and convert it to the namedtuple we need
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    raise TypeError("Model {} does not have valid format".format(mod))

    def reset_params(self):
        """
        Set all of the rendering parameters to their default settings.
        Run upon initialization but also allows the user to reset
        if they have made several changes and want to start fresh.

        Does not effect any of the underlying model data.
        """
        self.title_text = None
        self.show_header = True
        self.model_name = None
        self.column_labels = None
        self.column_separators = None
        self.show_model_nums = True
        self.original_param_names = None  # param names
        self.param_nicer_names = (
            None
        )  # nice_names: dic to map  params names to new displayable names
        self.show_precision = True
        self.show_sig = True  # show stars
        self.sig_levels = [0.1, 0.05, 0.03, 0.01]
        self.sig_digits = 3
        self.confidence_intervals = False
        self.show_footer = True
        self.custom_footer_text = []
        self.show_n = True
        self.show_r2 = True  # falses
        self.show_adj_r2 = True  # false
        self.show_residual_std_err = False  # false
        self.show_f_statistic = True  # false
        self.show_dof = False  #
        self.show_notes = True
        self.notes_label = "Note:"
        self.notes_append = True
        self.custom_notes = []

    def extract_data(self):
        """
        Extract the values we need from the models and store
        for use or modification. They should not be able to
        be modified by any rendering parameters.
        """
        self.validate_input()
        self.model_data = []
        for m in self.models:
            self.model_data.append(self.extract_model_data(m))

        pars = []
        for md in self.model_data:
            pars = pars + list(md["param_names"])
        self.param_names = sorted(set(pars))
        nlevels = self.models[0].params.index.nlevels
        # generate the first coluimn of table
        metalist = [[] for i in range(nlevels)]
        # ith list in the list is the ith index level value
        for i in range(nlevels):
            for p in self.param_names:
                if isinstance(pars[0], tuple):
                    metalist[i].append(p[i])
                else:
                    metalist[i].append(p)
        # the below list contains lists of indices where repeated
        # subsequent values are replaced by emppty string
        ulist = [[] for i in range(nlevels)]
        for i, l in enumerate(metalist):
            for j, n in enumerate(l):
                if j == 0:
                    ulist[i].append(str(n))
                elif j > 0:
                    if l[j] == l[j - 1]:
                        ulist[i].append("")
                    else:
                        ulist[i].append(str(n))
        df = pd.DataFrame(ulist).transpose()
        if isinstance(pars[0], tuple):
            df.index = pd.MultiIndex.from_tuples(self.param_names)
        else:
            df.index = self.param_names

        self.first_table_col = df

    def extract_model_data(self, model):  # assume model is namedtuple
        data = {}
        data["param_names"] = model.params.index.values
        data["param_values"] = model.params.value
        data["p_values"] = model.params.pvalue
        data["param_std_err"] = model.params.standard_error
        data["ci_lower"] = model.params.ci_lower
        data["ci_upper"] = model.params.ci_upper
        data["r2"] = model.info.get("rsquared", np.nan)
        data["r2_adj"] = model.info.get("rsquared_adj", np.nan)
        data["resid_std_err"] = np.sqrt(model.info.get("scale", np.nan))
        data["f_statistic"] = model.info.get("fvalue", np.nan)
        data["f_p_value"] = model.info.get("f_pvalue", np.nan)
        data["degree_freedom"] = model.info.get("df_model", np.nan)
        data["degree_freedom_resid"] = model.info.get("df_resid", np.nan)
        data["n_obs"] = model.info.get(
            "n_obs", data["degree_freedom"] + data["degree_freedom_resid"] + 1
        )
        data["dependent_variable"] = model.info.get("dependent_variable", np.nan)
        # generate significance icons
        sig_bins = [-1] + sorted(self.sig_levels) + [2]
        data["sig_icons"] = pd.cut(
            data["p_values"],
            bins=sig_bins,
            labels=[
                "*" * (len(self.sig_levels) - i)
                for i in range(len(self.sig_levels) + 1)
            ],
        )
        data["sig_icon_fstat"] = (
            "*"
            * (1 - np.isnan(data["f_p_value"]))
            * (len(self.sig_levels) - np.digitize(data["f_p_value"], sig_bins) + 1)
        )
        return data

    # Begin render option functions
    def title(self, title):
        self.title_text = title

    def show_header(self, show):
        assert type(show) == bool, "Please input True/False"
        self.header = show

    def show_model_numbers(self, show):
        assert type(show) == bool, "Please input True/False"
        self.show_model_nums = show

    def custom_columns(self, labels, separators=None):
        if separators is not None:
            assert (
                type(labels) == list
            ), "Please input a list of labels or a single label string"
            assert type(separators) == list, "Please input a list of column separators"
            assert len(labels) == len(
                separators
            ), "Number of labels must match number of columns"
            assert (
                sum([int(type(s) != int) for s in separators]) == 0
            ), "Columns must be ints"
            assert (
                sum(separators) == self.num_models
            ), "Please set number of columns to number of models"
        else:
            assert (
                type(labels) == str
            ), "Please input a single string label if no columns specified"

        self.column_labels = labels
        self.column_separators = separators

    def significance_levels(self, levels):
        assert (
            sum([int(type(l) != float) for l in levels]) == 0
        ), "Please input floating point values as significance levels"
        self.sig_levels = sorted(levels, reverse=True)
        # Redefine the significance stars
        sig_bins = [-1] + sorted(self.sig_levels) + [2]
        for md in self.model_data:
            md["sig_icons"] = pd.cut(
                md["p_values"],
                bins=sig_bins,
                labels=[
                    "*" * (len(self.sig_levels) - i)
                    for i in range(len(self.sig_levels) + 1)
                ],
            )
            md["sig_icon_fstat"] = (
                "*"
                * (1 - np.isnan(md["f_p_value"]))
                * (len(self.sig_levels) - np.digitize(md["f_p_value"], sig_bins) + 1)
            )

    def significant_digits(self, digits):
        assert type(digits) == int, "The number of significant digits must be an int"
        assert digits < 10, "Whoa hold on there bud, maybe use fewer digits"
        self.sig_digits = digits

    def show_confidence_intervals(self, show):
        assert type(show) == bool, "Please input True/False"
        self.confidence_intervals = show

    def model_name(self, name):
        assert type(name) == str, "Please input a string to use as the model name"
        self.model_name = name

    def covariate_order(self, param_names):
        missing = set(param_names).difference(set(self.param_names))
        assert not missing, (
            "Parameter order must contain subset of existing "
            "parameters: {} are not.".format(missing)
        )
        self.original_param_names = self.param_names
        self.param_names = param_names

    def rename_covariates(self, param_nicer_names):
        assert isinstance(
            param_nicer_names, dict
        ), "Please input a dictionary with parameter names as keys"
        self.param_nicer_names = param_nicer_names

    def reset_covariate_order(self):
        if self.original_param_names is not None:
            self.param_names = self.original_param_names

    def show_degrees_of_freedom(self, show):
        assert type(show) == bool, "Please input True/False"
        self.show_dof = show

    def custom_note_label(self, notes_label):
        assert (
            type(notes_label) == str
        ), "Please input a string to use as the note label"
        self.notes_label = notes_label

    def add_custom_notes(self, notes):
        assert sum([int(type(n) != str) for n in notes]) == 0, "Notes must be strings"
        self.custom_notes = notes

    def append_notes(self, append):
        assert type(append) == bool, "Please input True/False"
        self.notes_append = append

    # Begin HTML render functions
    def render_html(self):
        html = ""
        html += self.generate_header_html()
        html += self.generate_body_html()
        html += self.generate_footer_html()

        return html

    def generate_header_html(self):
        header = ""
        if not self.show_header:
            return header

        if self.title_text is not None:
            header += self.title_text + "<br>"

        header += '<table style="text-align:center"><tr><td colspan="'
        header += (
            str(self.num_models + len(self.first_table_col.columns))
            + '" style="border-bottom: 1px solid black"></td></tr>'
        )
        if self.model_name is not None:
            header += '<tr><td style="text-align:left"></td><td colspan="' + str(
                self.num_models + len(self.first_table_col.columns) - 1
            )
            header += '"><em>' + self.model_name + "</em></td></tr>"

        header += '<tr><td style="text-align:left"></td>'

        if self.column_labels is not None:
            if type(self.column_labels) == str:
                if len(self.first_table_col.columns) > 1:
                    header += (
                        '<td colspan="'
                        + str(len(self.first_table_col.columns) - 1)
                        + '">'
                        + " </td>"
                    )
                header += '<td colspan="' + str(self.num_models) + '">'
                header += self.column_labels + "</td></tr>"
            else:
                # The first table column holds the covariates names:
                header += "<tr><td></td>"
                if len(self.first_table_col.columns) > 1:
                    header += (
                        '<td colspan="'
                        + str(len(self.first_table_col.columns) - 1)
                        + '">'
                        + "</td>"
                    )
                for i, label in enumerate(self.column_labels):
                    sep = self.column_separators[i]
                    header += '<td colspan="{}">{}</td>'.format(sep, label)
                header += "</tr>"

        if self.show_model_nums:
            header += '<tr><td style="text-align:left"></td>'
            if len(self.first_table_col.columns) > 1:
                header += (
                    '<td colspan="'
                    + str(len(self.first_table_col.columns) - 1)
                    + '">'
                    + "</td>"
                )
            for num in range(1, self.num_models + 1):
                header += "<td>(" + str(num) + ")</td>"
            header += "</tr>"
        if len(self.first_table_col.columns) > 1:
            header += '<tr><td colspan="' + str(
                self.num_models + len(self.first_table_col.columns) + 1
            )
        else:
            header += '<tr><td colspan="' + str(self.num_models + 1)
        header += '" style="border-bottom: 1px solid black"></td></tr>'

        return header

    def generate_body_html(self):
        """
        Generate the body of the results where the
        covariate reporting is.
        """
        body = ""
        for param_name in self.param_names:
            body += self.generate_param_rows_html(param_name)

        return body

    def generate_param_rows_html(self, param_name):
        param_text = ""
        param_text += self.generate_param_main_html(param_name)
        if self.show_precision:
            param_text += self.generate_param_precision_html(param_name)
        else:
            param_text += "<tr></tr>"

        return param_text

    def generate_param_main_html(self, param_name):
        # param_name is unique
        # names
        if isinstance(param_name, tuple):
            param_print_name = param_name[-1]
        else:
            param_print_name = param_name
        if self.param_nicer_names is not None:
            param_print_name = self.param_nicer_names.get(
                param_print_name, param_print_name
            )
        param_text = "<tr>"
        if not isinstance(param_name, tuple):
            param_text += (
                '<td style="text-align:left">' + param_print_name + "&nbsp;</td>"
            )
        else:
            for i in range(len(param_name) - 1):
                param_text += (
                    '<td style="text-align:left">'
                    + str(self.first_table_col.loc[param_name][i])
                    + "&nbsp;</td>"
                )
            param_text += (
                '<td style="text-align:left">' + param_print_name + "&nbsp;</td>"
            )
        # values
        for md in self.model_data:
            if param_name in list(md["param_names"]):
                param_text += "<td>"
                param_text += str(
                    np.round(md["param_values"][param_name], self.sig_digits)
                )
                if self.show_sig:
                    param_text += "<sup>" + str(md["sig_icons"][param_name]) + "</sup>"
                param_text += "</td>"
            else:
                param_text += "<td></td>"
        param_text += "</tr>"

        return param_text

    def generate_param_precision_html(self, param_name):

        param_text = '<tr><td style="text-align:left"></td>'
        if isinstance(param_name, tuple):
            param_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if param_name in list(md["param_names"]):
                param_text += "<td>&nbsp;("
                if self.confidence_intervals:
                    param_text += (
                        str(np.round(md["ci_lower"][param_name], self.sig_digits)) + " , "
                    )
                    param_text += str(
                        np.round(md["ci_upper"][param_name], self.sig_digits)
                    )
                else:
                    param_text += str(
                        np.round(md["param_std_err"][param_name], self.sig_digits)
                    )
                param_text += ")</td>"
            else:
                param_text += "<td></td>"
        param_text += "</tr>"

        return param_text

    def generate_footer_html(self):
        """
        Generate the footer of the table where
        model summary section is.
        """
        footer = (
            '<td colspan="'
            + str(self.num_models + len(self.first_table_col.columns))
            + '" style="border-bottom: 1px solid black"></td></tr>'
        )

        if not self.show_footer:
            return footer
        footer += self.generate_observations_html()
        footer += self.generate_r2_html()
        footer += self.generate_r2_adj_html()
        if self.show_residual_std_err:
            footer += self.generate_resid_std_err_html()
        if self.show_f_statistic:
            footer += self.generate_f_statistic_html()
        footer += (
            '<tr><td colspan="'
            + str(self.num_models + len(self.first_table_col.columns))
            + '" style="border-bottom: 1px solid black"></td></tr>'
        )
        footer += self.generate_notes_html()
        footer += "</table>"

        return footer

    def generate_observations_html(self):
        obs_text = ""
        if not self.show_n:
            return obs_text
        obs_text += '<tr><td style="text-align: left">Observations</td>'
        if len(self.first_table_col.columns) > 1:
            obs_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if np.isnan(md["n_obs"]):
                obs_text += "<td>  </td>"
            else:
                obs_text += "<td>" + str(md["n_obs"]) + "</td>"

        obs_text += "</tr>"
        return obs_text

    def generate_r2_html(self):
        r2_text = ""
        if not self.show_r2:
            return r2_text
        r2_text += '<tr><td style="text-align: left">R<sup>2</sup></td>'
        if len(self.first_table_col.columns) > 1:
            r2_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if np.isnan(md["r2"]):
                r2_text += "<td> </td>"
            else:
                r2_text += "<td>" + str(np.round(md["r2"], self.sig_digits)) + "</td>"
        r2_text += "</tr>"
        return r2_text

    def generate_r2_adj_html(self):
        r2_text = ""
        if not self.show_r2:
            return r2_text
        r2_text += '<tr><td style="text-align: left">Adjusted R<sup>2</sup></td>'
        if len(self.first_table_col.columns) > 1:
            r2_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if np.isnan(md["r2_adj"]):
                r2_text += "<td>  </td>"
            else:
                r2_text += "<td>" + str(np.round(md["r2_adj"], self.sig_digits)) + "</td>"
        r2_text += "</tr>"
        return r2_text

    def generate_resid_std_err_html(self):
        rse_text = ""
        if not self.show_r2:
            return rse_text
        rse_text += '<tr><td style="text-align: left">Residual Std. Error</td>'
        if len(self.first_table_col.columns) > 1:
            rse_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if np.isnan(md["resid_std_err"]):
                rse_text += "<td> "
            else:
                rse_text += "<td>" + str(np.round(md["resid_std_err"], self.sig_digits))
                if self.show_dof and not np.isnan(md["degree_freedom_resid"]):
                    rse_text += "(df = " + str(np.round(md["degree_freedom_resid"])) + ")"
            rse_text += "</td>"
        rse_text += "</tr>"
        return rse_text

    def generate_f_statistic_html(self):
        f_text = ""
        if not self.show_r2:
            return f_text
        f_text += '<tr><td style="text-align: left">F Statistic</td>'
        if len(self.first_table_col.columns) > 1:
            f_text += (
                '<td colspan="'
                + str(len(self.first_table_col.columns) - 1)
                + '">'
                + "</td>"
            )
        for md in self.model_data:
            if np.isnan(md["f_statistic"]):
                f_text += "<td>"
            else:
                f_text += "<td>" + str(np.round(md["f_statistic"], self.sig_digits))
                f_text += "<sup>" + md["sig_icon_fstat"] + "</sup>"
                if self.show_dof:
                    ind_df = np.isnan(md["degree_freedom"])
                    ind_dfr = np.isnan(md["degree_freedom_resid"])
                    ind = min(ind_df, ind_dfr)
                    f_text += (1 - ind) * (
                        "(df = "
                        + (1 - ind_df) * str(md["degree_freedom"])
                        + "; "
                        + (1 - ind_dfr) * str(md["degree_freedom_resid"])
                        + ")"
                    )
            f_text += "</td>"
        f_text += "</tr>"
        return f_text

    def generate_notes_html(self):
        notes_text = ""
        if not self.show_notes:
            return notes_text

        notes_text += '<tr><td style="text-align: left">' + self.notes_label + "</td>"

        if self.notes_append:
            notes_text += self.generate_p_value_section_html()

        notes_text += "</tr>"

        notes_text += self.generate_additional_notes_html()

        return notes_text

    def generate_p_value_section_html(self):
        sig_levels = sorted(self.sig_levels)
        notes_text = """
 <td colspan="{}" style="text-align: right">""".format(
            self.num_models + len(self.first_table_col.columns) - 1
        )
        for i in range(len(sig_levels) - 1):
            notes_text += (
                "<sup>"
                + "*" * (len(sig_levels) - i)
                + """</sup>p&lt;{}; """.format(sig_levels[i])
            )
        notes_text += """<sup>*</sup>p&lt;{} </td>""".format(sig_levels[-1])
        return notes_text

    def generate_additional_notes_html(self):
        notes_text = ""
        if len(self.custom_notes) == 0:
            return notes_text
        for i, note in enumerate(self.custom_notes):
            if (i != 0) or (self.notes_append):
                notes_text += "<tr>"
            notes_text += (
                '<td></td><td colspan="'
                + str(self.num_models + len(self.first_table_col.columns) - 1)
                + '" style="text-align: right">'
                + note
                + "</td></tr>"
            )

        return notes_text

    # Begin LaTeX render functions
    def render_latex(self, only_tabular=False):
        latex = ""
        latex += self.generate_header_latex(only_tabular=only_tabular)
        latex += self.generate_body_latex()
        latex += self.generate_footer_latex(only_tabular=only_tabular)

        return latex

    def generate_header_latex(self, only_tabular=False):
        ncol = len(self.first_table_col.columns)
        header = ""
        if not only_tabular:
            header += "\\begin{table}[!htbp] \\centering\n"
            if not self.show_header:
                return header

            if self.title_text is not None:
                header += "  \\caption{" + self.title_text + "}\n"

            header += "  \\label{}\n"

        header += (
            "\\begin{tabularx}{\\textwidth}{"
            + ncol * "l"
            + self.num_models * "X"
            + "}\n"
        )
        header += "\\\\[-1.8ex]\\hline\n"
        header += "\\hline \\\\[-1.8ex]\n"
        if self.model_name is not None:
            header += "&" * ncol + "\\multicolumn{" + str(self.num_models) + "}{c}"
            header += "{\\textit{" + self.model_name + "}} \\\n"
            header += (
                "\\cr \\cline{"
                + str(self.num_models + 1)
                + "-"
                + str(self.num_models + ncol)
                + "}\n"
            )

        if self.column_labels is not None:
            if type(self.column_labels) == str:
                header += (
                    "\\\\[-1.8ex]"
                    + "&" * ncol
                    + "\\multicolumn{"
                    + str(self.num_models)
                    + "}{c}{"
                    + self.column_labels
                    + "} \\\\"
                )
            else:
                header += "\\\\[-1.8ex]" + (ncol - 1) * "&"
                for i, label in enumerate(self.column_labels):
                    header += "& \\multicolumn{" + str(self.column_separators[i])
                    header += "}{l}{" + label + "} "
                header += " \\\\\n"

        if self.show_model_nums:
            header += "\\\\[-1.8ex]" + (ncol - 1) * " &"
            for num in range(1, self.num_models + 1):
                header += "& (" + str(num) + ") "
            header += "\\\\\n"

        header += "\\hline \\\\[-1.8ex]\n"

        return header

    def generate_body_latex(self):
        """
        Generate the body of the results where the
        covariate reporting is.
        """
        body = ""
        for param_name in self.param_names:
            body += self.generate_param_rows_latex(param_name)
            body += "  "
            for _ in range(self.num_models):
                body += "& "
            body += "\\\\\n"

        return body

    def generate_param_rows_latex(self, param_name):
        param_text = ""
        param_text += self.generate_param_main_latex(param_name)
        if self.show_precision:
            param_text += self.generate_param_precision_latex(param_name)
        else:
            param_text += "& "

        return param_text

    def generate_param_main_latex(self, param_name):
        if isinstance(param_name, tuple):
            param_print_name = param_name[-1]
        else:
            param_print_name = param_name
        if self.param_nicer_names is not None:
            param_print_name = self.param_nicer_names.get(
                param_print_name, param_print_name
            )

        if not isinstance(param_name, tuple):
            param_text = " " + param_print_name + " "
        else:
            param_text = " "
            for i in range(len(param_name) - 1):
                param_text += str(self.first_table_col.loc[param_name][i]) + "&"
            param_text += param_print_name
        for md in self.model_data:
            if param_name in list(md["param_names"]):
                param_text += "& " + str(
                    np.round(md["param_values"][param_name], self.sig_digits)
                )
                if self.show_sig:
                    param_text += "$^{" + str(md["sig_icons"][param_name]) + "}$"
                param_text += " "
            else:
                param_text += "& "
        param_text += "\\\\\n"

        return param_text

    def generate_param_precision_latex(self, param_name):
        param_text = "&" * (len(self.first_table_col.columns) - 1)
        for md in self.model_data:
            if param_name in list(md["param_names"]):
                param_text += "&("
                if self.confidence_intervals:
                    param_text += (
                        str(np.round(md["ci_lower"][param_name], self.sig_digits)) + " , "
                    )
                    param_text += str(
                        np.round(md["ci_upper"][param_name], self.sig_digits)
                    )
                else:
                    param_text += str(
                        np.round(md["param_std_err"][param_name], self.sig_digits)
                    )
                param_text += ")"
            else:
                param_text += "& "
        param_text += "\\\\\n"

        return param_text

    def generate_footer_latex(self, only_tabular=False):
        """
        Generate the footer of the table where
        model summary section is.
        """

        footer = "\\hline \\\\[-1.8ex]\n"

        if not self.show_footer:
            return footer
        footer += self.generate_observations_latex()
        footer += self.generate_r2_latex()
        footer += self.generate_r2_adj_latex()
        if self.show_residual_std_err:
            footer += self.generate_resid_std_err_latex()
        if self.show_f_statistic:
            footer += self.generate_f_statistic_latex()
        footer += "\\hline\n\\hline \\\\[-1.8ex]\n"
        footer += self.generate_notes_latex()
        footer += "\\end{tabularx}"

        if not only_tabular:
            footer += "\n\\end{table}"

        return footer

    def generate_observations_latex(self):
        obs_text = ""
        if not self.show_n:
            return obs_text
        obs_text += " Observations\\quad\\quad " + "&" * (
            len(self.first_table_col.columns) - 1
        )
        for md in self.model_data:
            if np.isnan(md["n_obs"]):
                obs_text += "&   "
            else:
                obs_text += "& " + str(md["n_obs"]) + " "
        obs_text += "\\\\\n"
        return obs_text

    def generate_r2_latex(self):
        r2_text = ""
        if not self.show_r2:
            return r2_text
        r2_text += " R${2}$\\quad\\quad " + "&" * (
            len(self.first_table_col.columns) - 1
        )
        for md in self.model_data:
            if np.isnan(md["r2"]):
                r2_text += "&   "
            else:
                r2_text += "& " + str(np.round(md["r2"], self.sig_digits)) + " "
        r2_text += "\\\\\n"
        return r2_text

    def generate_r2_adj_latex(self):
        r2_text = ""
        if not self.show_r2:
            return r2_text
        r2_text += " Adjusted R${2}$\\quad\\quad" + "&" * (
            len(self.first_table_col.columns) - 1
        )
        for md in self.model_data:
            if np.isnan(md["r2_adj"]):
                r2_text += "&   "
            else:
                r2_text += "& " + str(np.round(md["r2_adj"], self.sig_digits)) + " "
        r2_text += "\\\\\n"
        return r2_text

    def generate_resid_std_err_latex(self):
        rse_text = ""
        if not self.show_r2:
            return rse_text
        rse_text += " Residual Std. Error \\quad\\quad" + "&" * (
            len(self.first_table_col.columns) - 1
        )
        for md in self.model_data:
            if np.isnan(md["resid_std_err"]):
                rse_text += "&  "
            else:
                rse_text += "& " + str(np.round(md["resid_std_err"], self.sig_digits))
                if self.show_dof and not np.isnan(md["degree_freedom_resid"]):
                    rse_text += "(df = " + str(np.round(md["degree_freedom_resid"])) + ")"
            rse_text += " "
        rse_text += " \\\\\n"
        return rse_text

    def generate_f_statistic_latex(self):
        f_text = ""
        if not self.show_r2:
            return f_text

        f_text += " F Statistic\\quad\\quad " + "&" * (
            len(self.first_table_col.columns) - 1
        )

        for md in self.model_data:
            if np.isnan(md["f_statistic"]):
                f_text += "&    "
            else:
                f_text += "& " + str(np.round(md["f_statistic"], self.sig_digits))
                f_text += "$^{" + md["sig_icon_fstat"] + "}$ "
                if self.show_dof:
                    ind_df = np.isnan(md["degree_freedom"])
                    ind_dfr = np.isnan(md["degree_freedom_resid"])
                    ind = min(ind_df, ind_dfr)
                    f_text += (1 - ind) * (
                        "(df = "
                        + (1 - ind_df) * str(md["degree_freedom"])
                        + "; "
                        + (1 - ind_dfr) * str(md["degree_freedom_resid"])
                        + ")"
                    )
            f_text += " "
        f_text += "\\\\\n"
        return f_text

    def generate_notes_latex(self):
        notes_text = ""
        if not self.show_notes:
            return notes_text

        notes_text += "\\textit{" + self.notes_label + "}"

        if self.notes_append:
            notes_text += self.generate_p_value_section_latex()
        notes_text += self.generate_additional_notes_latex()

        return notes_text

    def generate_p_value_section_latex(self):
        sig_levels = sorted(self.sig_levels)
        notes_text = ""
        notes_text += (
            " & \\multicolumn{"
            + str(self.num_models + len(self.first_table_col.columns) - 1)
            + "}{r}{"
        )
        for i in range(len(sig_levels) - 1):
            notes_text += (
                "$^{"
                + "*" * (len(sig_levels) - i)
                + "}$p$<$"
                + str(sig_levels[i])
                + "; "
            )
        notes_text += "$^{*}$p$<$" + str(sig_levels[-1]) + "} \\\\\n"
        return notes_text

    def generate_additional_notes_latex(self):
        notes_text = ""
        # if len(self.custom_notes) == 0:
        #     return notes_text
        for note in self.custom_notes:
            # if (i != 0) | (self.notes_append):
            #     notes_text += '\\multicolumn{' + str(self.num_models) + '}{r}\\textit{' + note + '} \\\\\n'
            # else:
            #     notes_text += ' & \\multicolumn{' + str(self.num_models) + '}{r}\\textit{' + note + '} \\\\\n'
            notes_text += (
                " &" * (len(self.first_table_col.columns))
                + "\\multicolumn{"
                + str(self.num_models)
                + "}{r}\\textit{"
                + note
                + "} \\\\\n"
            )

        return notes_text

    # Begin Markdown render functions
    # def render_markdown(self):
    #     print("sorry haven't made this yet :/")

    # Begin ASCII render functions
    # def render_ascii(self):
    #     print("sorry haven't made this yet :/")
