#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "fastyaml/yaml_parser.hpp"
#include <memory>
#include <string>

namespace py = pybind11;
using namespace fastyaml;

// Forward declaration
py::object yaml_value_to_python(const YamlValue& value,
    std::unordered_map<void*, py::object>* seen = nullptr);

// Convert C++ Mapping to Python dict (with identity cache for aliases)
py::dict mapping_to_dict(const Mapping& mapping,
    std::unordered_map<void*, py::object>* seen) {
    void* ptr = const_cast<Mapping*>(&mapping);  // same object = same address for alias identity
    if (ptr && seen) {
        auto it = seen->find(ptr);
        if (it != seen->end()) return py::reinterpret_borrow<py::dict>(it->second);
    }
    py::dict result;
    if (ptr && seen) (*seen)[ptr] = result;
    for (const auto& [key, value] : mapping.values) {
        result[py::str(key)] = yaml_value_to_python(value, seen);
    }
    return result;
}

// Convert C++ YamlValue to Python object (with identity cache for aliases)
py::object yaml_value_to_python(const YamlValue& value,
    std::unordered_map<void*, py::object>* seen) {
    if (!seen) {
        std::unordered_map<void*, py::object> cache;
        return yaml_value_to_python(value, &cache);
    }
    return std::visit([seen](auto&& arg) -> py::object {
        using T = std::decay_t<decltype(arg)>;

        if constexpr (std::is_same_v<T, Null>) {
            return py::none();
        } else if constexpr (std::is_same_v<T, Integer>) {
            return py::cast(arg);
        } else if constexpr (std::is_same_v<T, Float>) {
            return py::cast(arg);
        } else if constexpr (std::is_same_v<T, Boolean>) {
            return py::cast(arg);
        } else if constexpr (std::is_same_v<T, String>) {
            return py::cast(arg);
        } else if constexpr (std::is_same_v<T, MappingPtr>) {
            return mapping_to_dict(*arg, seen);
        } else if constexpr (std::is_same_v<T, SequencePtr>) {
            void* ptr = arg.get();
            if (ptr && seen) {
                auto it = seen->find(ptr);
                if (it != seen->end()) return py::reinterpret_borrow<py::list>(it->second);
            }
            py::list result;
            if (ptr && seen) (*seen)[ptr] = result;
            for (const auto& elem : arg->elements) {
                result.append(yaml_value_to_python(elem, seen));
            }
            return result;
        }
    }, value);
}

// Python loads function
py::object loads(const std::string& yaml_string) {
    YamlParser parser;
    YamlValue result = parser.parse(yaml_string);

    if (parser.has_error()) {
        throw std::runtime_error("YAML parse error: " + parser.get_error());
    }

    return yaml_value_to_python(result);
}

// Python load_all function
py::list load_all(const std::string& yaml_string) {
    YamlParser parser;
    std::vector<YamlValue> docs = parser.parse_all(yaml_string);

    if (parser.has_error()) {
        throw std::runtime_error("YAML parse error: " + parser.get_error());
    }

    py::list result;
    for (const auto& doc : docs) {
        result.append(yaml_value_to_python(doc));
    }
    return result;
}

PYBIND11_MODULE(_native, m) {
    m.doc() = "Fast YAML parser for Python with C++/SIMD backend";

    m.def("loads", &loads, R"pbdoc(
        Parse a YAML string and return a dictionary or list.

        Args:
            yaml_string: The YAML string to parse

        Returns:
            dict or list: Parsed YAML data (PyYAML compatible)

        Raises:
            RuntimeError: If parsing fails
    )pbdoc", py::arg("yaml_string"));

    m.def("load_all", &load_all, R"pbdoc(
        Parse all YAML documents in a multi-document stream.

        Args:
            yaml_string: The YAML string (may contain --- document separators)

        Returns:
            list: List of parsed documents (PyYAML load_all compatible)

        Raises:
            RuntimeError: If parsing fails
    )pbdoc", py::arg("yaml_string"));

    m.attr("__version__") = "0.1.0";
}
