import numpy as np
from scipy.stats import entropy


class GroupEvaluation:
    def __init__(self, foreigners, groups):
        self.foreigners = foreigners
        self.n_students = len(foreigners)

        self.groups = groups
        self.n_group_opt = self.n_students / len(self.groups)

    # Mapping for the last day
    def last_comb(self, combs: np.ndarray):
        return np.apply_along_axis(lambda x: np.setdiff1d(self.groups, x), axis=0, arr=combs)

    def error_group_sizes(self, combs: np.ndarray):
        errors = []

        for comb in combs:
            counts = np.unique(comb, return_counts=True)[1]
            if len(counts) < len(self.groups):
                # At least one slot did not get a student at all --> max error
                errors.append(1)

            # Use the difference to the optimal solution as error
            diffs = np.abs(counts - self.n_group_opt)
            # The weakest group size counts (all groups should have an equal number of members)
            diffs = np.max(diffs)
            # Norm to [0;1]
            errors.append(diffs / self.n_group_opt)

        # The group sizes should be good on every day
        return max(errors)

    def error_diffusion(self, combs: np.ndarray):
        confusions = np.zeros(self.n_students)

        for i in range(self.n_students):
            others_indices = set()

            for comb in combs:
                # At each day, find the other team members (they are assigned to the same group number as the current student)
                others_indices.update(np.where(comb == comb[i])[0])

            confusions[i] = len(others_indices)

        # The student with the lowest confusion counts (all should be high)
        return 1 - np.min(confusions) / self.n_students

    def error_foreigners(self, combs:np.ndarray):
        errors = []

        for comb in combs:
            entropies = []
            for group in self.groups:
                group_members_indices = np.where(comb == group)[0]
                if len(group_members_indices) == 0:
                    entropies.append(0)
                    continue

                foreigners_group = self.foreigners[group_members_indices]

                # Calculate the fraction of foreigners and non-foreigners per group
                probabilities = np.zeros(2)
                unique, counts = np.unique(foreigners_group, return_counts=True)
                for value, count in zip(unique, counts):
                    probabilities[value] = count / len(foreigners_group)

                # The entropy is highest for the fraction (0.5, 0.5) which corresponds to a very well distributed group
                # It is lowest for e.g. (1, 0) which means that one group consists e.g. only of foreigners
                entropies.append(entropy(probabilities, base=2.0))

            # All groups should be well distributed, i.e. only the lowest entropy counts
            errors.append(1 - np.min(entropies))

        # The distribution should be good on every day
        return max(errors)

    def error_total(self, combs: np.ndarray):
        combs = np.vstack([combs, self.last_comb(combs)])

        return [self.error_group_sizes(combs), self.error_diffusion(combs), self.error_foreigners(combs)]
