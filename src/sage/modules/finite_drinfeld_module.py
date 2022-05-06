r"""
This module provides classes for finite Drinfeld modules
(`FiniteDrinfeldModule`) and their module action on the algebraic
closure of `\Fq` (`FiniteDrinfeldModuleAction`).

AUTHORS:

- Antoine Leudière (2022-04): initial version

Let `\tau` be the `\Fq`-linear Frobenius endomorphism of `\Fqbar`
defined by `x \mapsto x^q`. Let `L\{\tau\}` be the ring of Ore
polynomials in `\tau` with coefficients in L. Fix an element `\omega` in
`L` (global parameter). A finite Drinfeld module is an `\Fq`-algebra
morphism `\phi: \Fq[X] \to L\{\tau\]` such that:
    - the constant coefficient of `\phi(X)` is `\omega`,
    - there exists at least one `a \in \Fq[X]` such that `\phi(a)` has a
      non zero `\tau`-degree.

As an `\Fq[X]`-algebra morphism, a finite Drinfeld module is only
determined by the image of `X`.

Crucially, the Drinfeld module `\phi` gives rise to the `\Fq[X]`-module
law on `\Fqbar` defined by `(a, x) = \phi(a)(x)`.
"""

#*****************************************************************************
#       Copyright (C) 2022 Antoine Leudière <antoine.leudiere@inria.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.categories.action import Action
from sage.categories.homset import Hom
from sage.misc.latex import latex
from sage.rings.morphism import RingHomomorphism_im_gens
from sage.rings.polynomial.ore_polynomial_element import OrePolynomial
from sage.rings.polynomial.ore_polynomial_ring import OrePolynomialRing
from sage.rings.polynomial.polynomial_ring import PolynomialRing_dense_finite_field


class FiniteDrinfeldModule(RingHomomorphism_im_gens):
    r"""
    Class for finite Drinfeld modules.

    INPUT:

    - ``polring`` -- the base polynomial ring
    - ``gen`` -- the image of `X`

    EXAMPLES:
        
    .. RUBRIC:: Basics

    First, create base objects::

        sage: Fq = GF(7^2)
        sage: FqX.<X> = Fq[]
        sage: L = Fq.extension(3)
        sage: frobenius = L.frobenius_endomorphism(2)
        sage: Ltau.<t> = OrePolynomialRing(L, frobenius)

    Then we instanciate the Drinfeld module::

        sage: phi_X = 1 + t^2
        sage: phi = FiniteDrinfeldModule(FqX, phi_X)
        sage: phi
        Finite Drinfeld module from Univariate Polynomial Ring in X over Finite Field in z2 of size 7^2 over Finite Field in z6 of size 7^6 generated by t^2 + 1.

    There are getters for the base objects::

        sage: phi.polring()
        Univariate Polynomial Ring in X over Finite Field in z2 of size 7^2
        sage: phi.ore_polring()
        Ore Polynomial Ring in t over Finite Field in z6 of size 7^6 twisted by z6 |--> z6^(7^2)
        sage: phi.gen()
        t^2 + 1

    And the class inherits `RingHomomorphism_im_gens`, so that one can
    use::

        sage: phi.domain()
        Univariate Polynomial Ring in X over Finite Field in z2 of size 7^2
        sage: phi.codomain()
        Ore Polynomial Ring in t over Finite Field in z6 of size 7^6 twisted by z6 |--> z6^(7^2)
        sage: phi.im_gens()
        [t^2 + 1]

    The rank of the Drinfeld module is retrieved with::

        sage: phi.rank()
        2

    .. RUBRIC:: The module law induced by a Drinfeld module

    The most important feature of Drinfeld modules is that they induce
    an `\Fq[X]`-module law on the algebraic closure `\Fqbar` of `\Fq`.
    We implement this action for any finite field extension `M` of `L`.
    The `_get_action_` method returns an `Action` object::

        sage: M = L.extension(2)
        sage: action = phi._get_action_(M)
        sage: action
        Action on Finite Field in z12 of size 7^12 induced by the Finite Drinfeld module from Univariate Polynomial Ring in X over Finite Field in z2 of size 7^2 over Finite Field in z6 of size 7^6
        generated by t^2 + 1.
        sage: x = M.gen()
        sage: g = X^3 + X + 5
        sage: action(g, x)
        ...
        6*z12^11 + 5*z12^9 + 5*z12^8 + 2*z12^7 + 6*z12^6 + z12^5 + 6*z12^4 + 2*z12^3 + 3*z12^2 + 5*z12 + 4

    Furthermore, it can be useful to embed a Drinfeld module into a
    larger Ore polynomial ring::

        sage: M = L.extension(2)
        sage: psi = phi.change_ring(M); psi
        Finite Drinfeld module from Univariate Polynomial Ring in X over Finite Field in z2 of size 7^2 over Finite Field in z12 of size 7^12 generated by t^2 + 1.

        .. NOTE::

        The general definition of a Drinfeld module is out of the scope
        of this implementation.

    ::

        You can see all available methods of `RingHomomorphism_im_gens`
        with `dir(sage.rings.morphism.RingHomomorphism_im_gens)`. Same
        for `Action`.

    .. SEEALSO::
        :mod:`sage.categories.action.Action`
        :mod:`sage.rings.polynomial.ore_polynomial_element`
        :mod:`sage.rings.polynomial.ore_polynomial_ring`
    """
    
    def __init__(self, polring, gen):
        # VERIFICATIONS
        # Check `polring` is an Fq[X]:
        # See docstrings of `PolynomialRing_dense_finite_field` and
        # `is_PolynomialRing`.
        isinstance(polring, PolynomialRing_dense_finite_field)
        # Check `gen` is an Ore polynomial:
        if not isinstance(gen, OrePolynomial):
            raise TypeError('The generator must be an Ore polynomial')
        # Now we can define those for convenience:
        FqX = polring
        Ltau = gen.parent()
        Fq = FqX.base_ring()
        L = Ltau.base_ring()
        # Check the Ore polynomial ring is an L{tau} with L a finite
        # field extension of Fq:
        _check_base_fields(Fq, L)
        if not Ltau.twisting_derivation() is None:
            raise ValueError('The Ore polynomial ring should have no ' \
                    'derivation')
        # Check the frobenius is x -> x^q:
        if Ltau.twisting_morphism().power() != Fq.degree():
            raise ValueError('The twisting morphism of the Ore polynomial ' \
                    'ring must be the Frobenius endomorphism of the base ' \
                    'field of the polynomial ring')
        # The generator is not constant:
        if gen.is_constant():
            raise ValueError('The generator must not be constant')
        # ACTUAL WORK
        super().__init__(Hom(FqX, Ltau), gen)

    ###########
    # Methods #
    ###########

    def change_ring(self, R):
        # VERIFICATIONS
        if not R.is_field() and R.is_finite():
            raise TypeError('Argument must be a finite field')
        if not self.ore_polring().base_ring().is_subring(R):
            raise ValueError('The new field must be a finite field ' \
                    'extension of the base field of the Ore polynomial ring.')
        _check_base_fields(self.polring().base_ring(), R)
        # ACTUAL WORK
        new_frobenius = R.frobenius_endomorphism(self.frobenius().power())
        new_ore_polring = OrePolynomialRing(R, new_frobenius,
                names=self.ore_polring().variable_names())
        return FiniteDrinfeldModule(self.polring(), new_ore_polring(self.gen()))

    def rank(self):
        return self.gen().degree()

    ##########################
    # Special Sage functions #
    ##########################

    def _get_action_(self):
        return FiniteDrinfeldModuleAction(self)

    def _latex_(self):
        return f'\\text{{Finite{{ }}{latex(self.polring())}-Drinfeld{{ }}' \
                f'module{{ }}defined{{ }}by{{ }}}}\n' \
                f'\\begin{{align}}\n' \
                f'  {latex(self.polring())}\n' \
                f'  &\\to {latex(self.ore_polring())} \\\\\n' \
                f'  {latex(self.polring().gen())}\n' \
                f'  &\\mapsto {latex(self.gen())}\n' \
                f'\\end{{align}}\n' \
                f'\\text{{with{{ }}characteristic{{ }}}} ' \
                f'{latex(self.characteristic())}'

    def _repr_(self):
        return f'Finite Drinfeld module from {self.polring()} over ' \
                f'{self.ore_polring().base_ring()} generated by {self.gen()}.'

    ###########
    # Getters #
    ###########

    def frobenius(self):
        return self.ore_polring().twisting_morphism()

    def gen(self):
        [gen] = self.im_gens()
        return gen

    def ore_polring(self):
        return self.codomain()

    def polring(self):
        return self.domain()

class FiniteDrinfeldModuleAction(Action):

    def __init__(self, finite_drinfeld_module):
        # Verifications
        if not isinstance(finite_drinfeld_module, FiniteDrinfeldModule):
            raise TypeError('First argument must be a FiniteDrinfeldModule')
        # Work
        self.__finite_drinfeld_module = finite_drinfeld_module
        super().__init__(finite_drinfeld_module.polring(),
                finite_drinfeld_module.ore_polring().base_ring())

    ###########
    # Methods #
    ###########

    def finite_drinfeld_module(self):
        return self.__finite_drinfeld_module

    ##########################
    # Special Sage functions #
    ##########################

    def _latex_(self):
        return f'\\text{{Action{{ }}on{{ }}}}' \
                f'{latex(self.extension())}\\text{{{{ }}' \
                f'induced{{ }}by{{ }}}}{self.finite_drinfeld_module()}'

    def _repr_(self):
        return f'Action on {self.domain()} induced by ' \
                f'{self.finite_drinfeld_module()}'

    def _act_(self, g, x):
        return self.finite_drinfeld_module()(g)(x)


def _check_base_fields(Fq, L):
    if not (L.is_field() and L.is_finite() and Fq.is_subring(L)):
        raise ValueError(f'The base field of the Ore polynomial ring must ' \
                'be a finite field extension of the base field of the ' \
                'polynomial ring')
