(function () {
    "use strict";

    function getMaxNumber(inlineGroup) {
        var max = 0;
        inlineGroup.querySelectorAll("input[name$='-number']").forEach(function (input) {
            var val = parseInt(input.value, 10);
            if (!isNaN(val) && val > max) {
                max = val;
            }
        });
        return max;
    }

    document.addEventListener("formset:added", function (event) {
        var row = event.target;
        var numberInput = row.querySelector("input[name$='-number']");
        if (!numberInput) return;

        var inlineGroup = row.closest(".inline-group");
        if (!inlineGroup) return;

        var nextNum = getMaxNumber(inlineGroup) + 1;
        numberInput.value = nextNum;
    });
})();
