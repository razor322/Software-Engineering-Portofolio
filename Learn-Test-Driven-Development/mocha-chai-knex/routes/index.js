var express = require("express");
const queries = require("../db/queries");
var router = express.Router();

/* GET home page. */
router.get("/", function (req, res, next) {
  res.render("index", { title: "Express" });
});

// *** GET all shows *** //
router.get("/shows", function (req, res, next) {
  queries
    .getAll()
    .then(function (shows) {
      res.status(200).json(shows);
    })
    .catch(function (err) {
      next(err);
    });
});

// *** GET single show *** //
router.get("/shows/:id", function (req, res, next) {
  queries
    .getSingle(req.params.id)
    .then(function (show) {
      res.status(200).json(show);
    })
    .catch(function (err) {
      next(err);
    });
});
// *** POST single show *** //
router.post("/shows", function (req, res, next) {
  queries
    .add(req.body)
    .then(function (showID) {
      var id = showID[0] && showID[0].id ? showID[0].id : showID[0] || showID;
      return queries.getSingle(id);
    })
    .then(function (show) {
      res.status(200).json(show);
    })
    .catch(function (err) {
      next(err);
    });
});

// *** update show *** //
router.put("/shows/:id", function (req, res, next) {
  if (req.body.hasOwnProperty("id")) {
    return res.status(422).json({
      error: "You cannot update the id field",
    });
  }
  queries
    .update(req.params.id, req.body)
    .then(function () {
      return queries.getSingle(req.params.id);
    })
    .then(function (show) {
      res.status(200).json(show);
    })
    .catch(function (error) {
      next(error);
    });
});
// *** delete show *** //
router.delete("/shows/:id", function (req, res, next) {
  queries
    .getSingle(req.params.id)
    .then(function (show) {
      queries
        .deleteItem(req.params.id)
        .then(function () {
          res.status(200).json(show);
        })
        .catch(function (error) {
          next(error);
        });
    })
    .catch(function (error) {
      next(error);
    });
});

module.exports = router;
